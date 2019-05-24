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
from .singletonClass import Token, URL
import requests
import json


kafka_producer = KafkaProducer(bootstrap_servers='127.0.0.1:9094',  # for local tests
                               # bootstrap_servers='kafka:9094',  # for swarm
                               client_id="iot_recovery_module",
                               value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                               )

kafka_consumer = KafkaConsumer(bootstrap_servers='127.0.0.1:9094',  # for local tests
                               # bootstrap_servers='kafka:9094',  # for swarm
                               auto_offset_reset='earliest',
                               value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                               )

kafka_consumer.subscribe(['FailureTopic'])

headers = {'Authorization': 'Token {}'.format(Token.get_instance())}

for message in kafka_consumer:
    json_object_message = message.value

    # I get all used resources of the faulty endpoint
    request_url = URL.DB_URL+'getUsageByEpShadow/{}/{}/'.format(
        json_object_message['endpoint_id'],
        json_object_message['shadow_id'])

    response = requests.get(url=request_url)

    if response.status_code == 200:
        res_usage_list = json.loads(response.text)['usages']

        for res_usage in res_usage_list:
            aux = json.loads(res_usage)  # serialize string to json object an store it into local var aux
            res_id = aux["resource"]

            # For every used resource we search a similar one
                # 1 - if found we update in the db the fields shadow, iot_connector, endpoint, resource, kafkatopic
                    # we send the new topic to the app

                # 2 - if not found notify the app this type of resource is not available in the shadow
                    # delete res usage from db

