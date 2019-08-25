from kafka import KafkaClient, KafkaProducer, KafkaConsumer
import time
import json
import requests

# This consumer recieves feedback of what is happenning inside the system when something occurs

kafka_consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9094', '127.0.0.1:9095'],
                               auto_offset_reset="latest",
                               value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                               )

kafka_consumer.subscribe(["LogTopic"])
for msg in kafka_consumer:
    print(msg.value)
