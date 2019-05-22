'''
This module will continuously listen to a kafka topic FailureTopic and make the fault tolerance logic
when a device is down or when a resource is down.
The message this Module will receive is a JSON-like message that the consumer will deserialize into JSON object:

{
    'endpoint_id': <id> (mandatory)
    'shadow_id': <id> (optional)
}

'''

from kafka import KafkaProducer, KafkaConsumer
import requests
import json


kafka_producer = KafkaProducer(bootstrap_servers='127.0.0.1:9094',
                               client_id="iot_recovery_module",
                               value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                               )

kafka_consumer = KafkaConsumer(bootstrap_servers='127.0.0.1:9094',
                               auto_offset_reset='earliest',
                               value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                               )

kafka_consumer.subscribe(['xTopic'])

# print(kafka_consumer.topics())

for message in kafka_consumer:
    json_object = message.value


    if ''

