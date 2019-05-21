"""This is a singleton class to store information of the current user session."""


class User:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not User.__instance:
            User()

        return User.__instance

    def __init__(self, us_id=None, us_tok=None, us_em=None):
        """ Virtually private constructor. """
        if User.__instance:
            raise Exception("This class is a singleton!")
        else:
            self.user_id = us_id
            self.user_token = us_tok
            self.user_email = us_em
            User.__instance = self

