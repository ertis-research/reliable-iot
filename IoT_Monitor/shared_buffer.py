import threading


class SharedBuffer(object):
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if not SharedBuffer.__instance:
            SharedBuffer()

        return SharedBuffer.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if SharedBuffer.__instance:
            raise Exception("This class is a singleton!")
        else:
            self.buffer = []  # This will be a buffer of JSON objects
            self.shared_semaphore = threading.Semaphore()
            SharedBuffer.__instance = self
