from shared_buffer import SharedBuffer
import threading
import json

# for debugging purposes
import logging
from logging.handlers import SysLogHandler
formatter = logging.Formatter('%(asctime)-15s %(name)-12s: %(levelname)-8s %(message)s')
logger = logging.getLogger('my_logger')
handler = SysLogHandler(address='/dev/log')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class KfkConsumer(threading.Thread):
    def __init__(self, consumer, *args, **kwargs):
        super(KfkConsumer, self).__init__(*args, **kwargs)
        self.kafka_consumer = consumer
        self.shared_buffer_object = SharedBuffer.get_instance()

    def run(self):
        """Reads messages from Kafka and stores them into a buffer"""
        sh_semaphore = self.shared_buffer_object.shared_semaphore
        sh_buffer = self.shared_buffer_object.buffer

        # MESSAGE EXAMPLE RECEIVED FROM KAFKA
        # {
        #   'operation': 'READ' / 'OBSERVE' / 'WRITE' / 'EXECUTE' / 'DELETE',
        #   'resource_accessing': '/3303/1/5700',
        #   'kafka_topic': 'a_topic_name_between_app_and_iot_monitor'
        # }

        for msg in self.kafka_consumer:
            sh_semaphore.acquire()
            logger.debug("[Leshan Monitor]: Kafka message received: {}".format(json.dumps(msg)))
            sh_buffer.append(msg)  # message received buffered as it is (JSON object)

            sh_semaphore.release()
