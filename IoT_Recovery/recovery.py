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
from logging.handlers import SysLogHandler
from singletonClass import Token, URL
import requests
import logging
import json


# for debugging purposes
formatter = logging.Formatter('%(asctime)-15s %(name)-12s: %(levelname)-8s %(message)s')
logger = logging.getLogger('my_logger')
handler = SysLogHandler(address='/dev/log')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


kafka_producer = KafkaProducer(#bootstrap_servers='127.0.0.1:9094',  # for local tests
                               bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                               client_id="iot_recovery_module",
                               value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                               )

kafka_consumer = KafkaConsumer(#bootstrap_servers='127.0.0.1:9094',  # for local tests
                               bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                               # auto_offset_reset='earliest',
                               value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                               )

kafka_consumer.subscribe(['FailureTopic'])

headers = {'Authorization': 'Token {}'.format(Token.get_instance())}


def recovery(app_id, usage_id, shadow_id, resource_accessing, operation, app_old_topic):
    # first we need to get the app data
    url_app = URL.DB_URL+'getApp/{}/'.format(app_id)
    resp_app = requests.get(url=url_app, headers=headers)
    app_data = json.loads(resp_app.text)['app']

    # For an used resource we tell the IoT Shadow Applications to search a similar logic or create a new one
    url = 'http://iotshadowapplications:80/action/'
    data = {
        'app_name': app_data['name'],
        'shadow_id': shadow_id,
        'resource_accessing': resource_accessing,
        'operation': operation
    }
    resp = requests.post(url=url, data=data, headers=headers)

    if resp.status_code == 200:
        new_kafka_topic_for_app = json.load(resp.text)['kafka_topic']

        kafka_producer.send("LogTopic", {"[Iot Recovery]": "Sending new topic to app."})

        # We send the app the new kafka topic
        kafka_producer.send(app_old_topic, {'new_kafka_topic': new_kafka_topic_for_app})
        logger.debug("Recovery: Send the new topic to the app. ({})".format(new_kafka_topic_for_app))

    else:
        # notify to the app through Kafka no more resource available.
        kafka_producer.send(app_old_topic, {"NOTIFICATION": "No resource available!"})

        # delete from the db the usage
        url_delete = URL.DB_URL + 'deleteUsageResource/{}/'.format(usage_id)
        requests.delete(url=url_delete, headers=headers)

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

        for res_usage in res_usage_list:
            aux_res_usage = json.loads(res_usage)  # serialize string to json object and store it into local var aux
            applications = aux_res_usage['applications']  # list of app ids using this resource

            for application in applications:
                kafka_producer.send("LogTopic", "Recovery for application {}".format(application))

                recovery(application,
                         aux_res_usage['_id'],
                         aux_res_usage['shadow'],
                         aux_res_usage['accessing'],
                         aux_res_usage['operation'],
                         aux_res_usage['kafka_topic']
                         )
    else:
        kafka_producer.send("LogTopic", {"[Iot Recovery]": "No apps using the faulty resources. No need to recovery"})
