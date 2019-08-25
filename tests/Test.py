from kafka import KafkaClient, KafkaProducer, KafkaConsumer
import time
import json
import requests


# Replace token with a valid one every time test is run
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1NjIxNzA3NzUsInNoYWRvd19pZCI6ImE3ZmNmMjhiLTUzOGMtNDg0Ni1hODhhLTJkMzk0ZGFiYTI2YiIsInR5cGUiOiJERVZJQ0UifQ.E06ZE77dAZccrjM4QA9jsbV4olZjDGnbtrQj6L5NpLQ"
headers = {'Authorization': "Token {}".format(token)}


# IoT Device data that will be registered
data = {
    'type': 'Leshan',
    'ip': 'leshan',
    'port': '8080',
    'token': token,
    'MAC': "123456",
    'shadow_id': "a7fcf28b-538c-4846-a88a-2d394daba26b"
    }


# Register Request
url = "http://127.0.0.1:8001/register/"
r = requests.post(url=url, data=data, headers=headers)
print(r.status_code, r.text)

#-------------------------------------REGISTRATION ENDS HERE-----------------------------------
time.sleep(10)


# We will simulate the petition of an application asking for an Operation on a specific resource
data = {
    'app_name': 'TestingApp1',
    'resource_accessing': '/3303/0/5700',
    'operation': 'OBSERVE'
    }

url = "http://127.0.0.1:8003/action/"
r = requests.post(url=url, data=data, headers=headers)


# The app constantly is reading the data recieved from the observation
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

