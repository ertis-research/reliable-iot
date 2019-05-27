"""This is a singleton class to store the component token and database urls."""

from kafka import KafkaAdminClient, KafkaProducer
import requests
import json


class URL:
    DB_URL = 'http://127.0.0.1:8080/'  # on local for tests
    # DB_URL = 'http://mongoapi:80/'  # on docker swarm


class Token:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not Token.__instance:
            Token()

        return Token.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Token.__instance:
            raise Exception("This class is a singleton!")
        else:
            req = requests.post(url=URL.DB_URL+'generateToken/',
                                data={'type': 'COMPONENT'})

            token_id = json.loads(req.text)['token']  # i get the id of the token
            req_token = requests.get(url=URL.DB_URL+'getTokenById/{}/'.format(token_id))
            token = json.loads(req_token.text)['token']

            self.token = token

            Token.__instance = self


class KfkProducer:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not KfkProducer.__instance:
            KfkProducer()

        return KfkProducer.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if KfkProducer.__instance:
            raise Exception("This class is a singleton!")
        else:
            KfkProducer.__instance = \
                KafkaProducer(bootstrap_servers='kafka:9094',
                              client_id='iot_shadow_applications',
                              value_serializer=lambda v: json.dumps(v).encode('utf-8')
                              )


class KfkAdminClient:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not KfkAdminClient.__instance:
            KfkAdminClient()

        return KfkAdminClient.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if KfkAdminClient.__instance:
            raise Exception("This class is a singleton!")
        else:
            KfkAdminClient.__instance =\
                KafkaAdminClient(bootstrap_servers='kafka:9094',
                                 client_id='iot_shadow_applications',
                                 )
