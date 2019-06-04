from .shared_buffer import SharedBuffer
import threading


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

            sh_buffer.append(msg)  # message received buffered as it is (JSON object)

            sh_semaphore.release()
