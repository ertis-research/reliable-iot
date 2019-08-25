from kafka import KafkaClient, KafkaProducer, KafkaConsumer
import time
import json
import requests

# This is another application that asks for a resource
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1NjEwMjc3NDEsInNoYWRvd19pZCI6IjA5ZTg4YmIwLThlN2EtNDU4MC04ODY2LTFiYTVlNTJiZTM1NiIsInR5cGUiOiJERVZJQ0UifQ.-IZTKxRTOi7YuvUjsbN-j74zMOP5ZmkzhZK6nUlon0w"
headers = {'Authorization': "Token {}".format(token)}

url = "http://127.0.0.1:8003/action/"

data = {
    'app_name': 'segundaAPP',
    'resource_accessing': '/3303/0/5700',
    'operation': 'OBSERVE'
    }

r = requests.post(url=url, data=data, headers=headers)

if r.status_code == 200:
    kafka_consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9094', '127.0.0.1:9095'],
                                   auto_offset_reset="latest",
                                   value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                   )

    kfk = json.loads(r.text)['kafka_topic']
    kafka_consumer.subscribe([kfk])

    print("Reading from kafka topic: {}".format(kfk))
    for mes in kafka_consumer:
        print(mes.value)
else:
    print(r.text)
