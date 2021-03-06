'''
This module will continuously listen to a kafka topic FailureTopic and make the fault tolerance logic
when a device is down or when a resource is down.
The message this Module will receive is a JSON-like message that the consumer will deserialize into JSON object:

{
    'endpoint_id': <id> (mandatory)
    'shadow_id': <id> (mandatory)
}
'''

from kafka import KafkaProducer, KafkaConsumer
from singletonClass import Token, URL
import uuid
import requests
import json


kafka_producer = KafkaProducer(bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                               value_serializer=lambda v: json.dumps(v).encode('utf-8')
                               )

kafka_consumer = KafkaConsumer(bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                               group_id="recovery",
                               auto_offset_reset="latest",
                               client_id=uuid.uuid4().__str__(),
                               value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                               )

kafka_consumer.subscribe(['FailureTopic'])

headers = {'Authorization': 'Token {}'.format(Token.get_instance().token)}


def recovery(app_list, usage_id, shadow_id, resource_accessing, operation, app_old_topic):

    # 1st: get the app data of the first app
    app_id = app_list[0]
    app_list.pop(0)  # we remove the first app from the list

    # we make recovery for the first app
    url_app = URL.DB_URL+'getApp/{}/'.format(app_id)
    resp_app = requests.get(url=url_app, headers=headers)
    app_data = json.loads(resp_app.text)['app']
    app_data = json.loads(app_data)  # we got a json of a json, need to serialize twice

    # delete the old usage from the db
    url_delete = URL.DB_URL + 'deleteUsageResource/{}/'.format(usage_id)
    requests.delete(url=url_delete, headers=headers)

    # For an used resource we tell the IoT Shadow Applications to search a similar logic or create a new one
    url = 'http://iotshadowapplications:80/action/'
    data = {
        'app_name': app_data['name'],
        'shadow_id': shadow_id,
        'resource_accessing': resource_accessing,
        'operation': operation
    }
    resp = requests.post(url=url, data=data, headers=headers)

    kafka_producer.send("LogTopic", "[Iot Recovery]: Getting new logic from ShadowApps: {}".format(resp.text))

    if resp.status_code == 200:
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Got the new topic."})

        aux_response_json_object = json.loads(resp.text)
        new_kafka_topic_for_app = aux_response_json_object['kafka_topic']
        new_usage_id = aux_response_json_object['usage_id']

        # We send to all aps the new kafka topic (all apps are reading from the old topic)
        kafka_producer.send(app_old_topic, {'new_kafka_topic': new_kafka_topic_for_app})
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Sending new topic to apps."})

        # updating the usage with the new apps
        url_update = URL.DB_URL + 'updateUsageResource/{}/'.format(new_usage_id)
        r = requests.post(url=url_update, data={"applications": json.dumps(app_list)}, headers=headers)
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Applications updated: {}, status code: {}".format(json.dumps(app_list), r.status_code)})

    else:
        # notify to all apps that no more resource available. (all apps are reading from the old topic)
        kafka_producer.send(app_old_topic, {"NOTIFICATION": "No resource available!"})
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Resource not available."})


for message in kafka_consumer:
    json_object_message = message.value
    kafka_producer.send("LogTopic",  {"[Iot Recovery]": "Message received."})

    # I get all used resources of the faulty endpoint
    request_url = URL.DB_URL+'getUsageByEpShadow/{}/{}/'.format(
        json_object_message['endpoint_id'],
        json_object_message['shadow_id'])

    response = requests.get(url=request_url, headers=headers)

    if response.status_code == 200:
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Got all resources that failed."})
        res_usage_list = json.loads(response.text)['usages']

        if res_usage_list:
            for res_usage in res_usage_list:
                aux_res_usage = json.loads(res_usage)  # serialize string to json object and store it into local var aux

                applications = aux_res_usage['applications']  # list of app ids using this resource

                recovery(applications,
                         aux_res_usage['_id'],
                         aux_res_usage['shadow'],
                         aux_res_usage['accessing'],
                         aux_res_usage['operation'],
                         aux_res_usage['kafka_topic']
                         )
        else:
            kafka_producer.send("LogTopic",
                                {"[Iot Recovery]": "No apps using the faulty resources. No need to recovery"})
    else:
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "No apps using the faulty resources. No need to recovery"})
