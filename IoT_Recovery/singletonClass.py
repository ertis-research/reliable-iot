import requests
import json


class URL:
    # DB_URL = 'http://127.0.0.1:8000/'  # on local for tests
    DB_URL = 'http://mongoapi:80/'  # on docker swarm


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
