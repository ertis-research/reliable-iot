from kafka import KafkaProducer, KafkaConsumer
from kafka_consumer_thread import KfkConsumer
from shared_buffer import SharedBuffer
import aux_functions
import sseclient  # install sseclient-py library
import requests
import urllib3
import json


kafka_observe_topics = {}  # "/3303/0/5700": "topic_name"


def get_data_stream(token, api_endpoint, device_data, shadow_device_id):
    """ Start REST streaming device events given a Nest token.  """

    kafka_producer = KafkaProducer(bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                                   client_id=device_data['_id'],
                                   value_serializer=lambda v: json.dumps(v).encode('utf-8')
                                   )

    kafka_consumer = KafkaConsumer(bootstrap_servers=['kafka1:9092', 'kafka2:9092'],
                                   value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                                   )

    # we start a thread that constantly reads from kafka
    kafka_consumer.subscribe([device_data['_id']])
    t = KfkConsumer(consumer=kafka_consumer, producer=kafka_producer)
    t.start()
    # t.join()

    headers = {
        'Accept': 'text/event-stream'
    }

    shared_buffer_object = SharedBuffer.get_instance()
    sh_semaphore = shared_buffer_object.shared_semaphore
    sh_buffer = shared_buffer_object.buffer

    http = urllib3.PoolManager()

    # get response, handling redirects (307) if needed
    response = http.request('GET', api_endpoint, headers=headers, preload_content=False, redirect=False)

    # RIGHT HERE WE NEED TO STORE ALL THE ENDPOINTS IN THE DB AND THEIR ASSOCIATED RESOURCES TOO
    endpoints_list = requests.get(url='http://{}:{}/api/clients'.format(device_data['ip'], device_data['port']))
    endpoints_list = json.loads(endpoints_list.text)

    aux_functions.store_endpoints_and_resources(endpoints_list, device_data['_id'], token)

    if response.status == 307:
        redirect_url = response.headers.get("Location")
        response = http.request('GET', redirect_url, headers=headers, preload_content=False, redirect=False)
    if response.status != 200:
        print("An error occurred! Response code is ", response.status)

    client = sseclient.SSEClient(response)

    for event in client.events():  # returns a generator
        event_type = event.event

        # Message check
        try:
            read_and_execute_action_from_buffer(sh_semaphore, sh_buffer, device_data, kafka_producer)

        except IndexError:
            # it means there's no message in the buffer
            sh_semaphore.release()

        # Event check
        if event_type == 'UPDATED':  # updates periodically incoming

            data_to_store = aux_functions.purge_update_data(event.data)
            data = {'event': json.dumps(data_to_store)}  # event data as JSON
            endpoint_id = aux_functions.get_endpoint_id(data_to_store['registrationId'], token)

            aux_functions.update_endpoint(endpoint_id, data, token)

        elif event_type == 'REGISTRATION':
            """
            event:  REGISTRATION
            {"endpoint":"c5","registrationId":"0hb0nPEAMz",
            "registrationDate":"2019-06-07T10:16:48Z","lastUpdate":"2019-06-07T10:16:48Z",
            "address":"10.255.0.2:42165","lwM2mVersion":"1.0","lifetime":30,"bindingMode":"U",
            "rootPath":"/",
            "objectLinks":[{"url":"/","attributes":{"rt":"oma.lwm2m"}},
                            {"url":"/1/0","attributes":{}},{"url":"/3/0","attributes":{}},
                            {"url":"/6/0","attributes":{}},
                            {"url":"/3303/0","attributes":{}}],
            "secure":false,
            "additionalRegistrationAttributes":{}}
            
            """
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Registration event."})
            endpoint = json.loads(event.data)
            aux_functions.store_endpoints_and_resources([endpoint], device_data['_id'], token)

        elif event_type == 'DEREGISTRATION':  # we do not delete the data, we set status to 0, which means, unavailable

            """
            {"endpoint":"abc","registrationId":"yT9iROs5NR",
            "registrationDate":"2019-06-07T10:53:16Z","lastUpdate":"2019-06-07T10:53:16Z",
            "address":"10.255.0.2:56554","lwM2mVersion":"1.0","lifetime":30,"bindingMode":"U","rootPath":"/",
            "objectLinks":[{"url":"/","attributes":{"rt":"oma.lwm2m"}},{"url":"/1/0","attributes":{}},
                            {"url":"/3/0","attributes":{}},{"url":"/6/0","attributes":{}},
                            {"url":"/3303/0","attributes":{}}],
            "secure":false,
            "additionalRegistrationAttributes":{}}
            """
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Deregistration event."})

            endpoint = json.loads(event.data)
            endpoint_id = aux_functions.get_endpoint_id(endpoint['registrationId'], token)
            aux_functions.update_endpoint(endpoint_id, {'status': 0}, token)

            failure_data_recovery = {  # for now this info will be enough (it may change)
                'shadow_id': shadow_device_id,
                'connector_id': device_data['_id'],
                'endpoint_id': endpoint_id
            }
            # inform to recovery shadow when a device has fallen down at topic FailureTopic
            kafka_producer.send('FailureTopic', failure_data_recovery)

        elif event_type == 'NOTIFICATION':
            # data_observed e.g. = {"ep": "C1", "res": "/3303/0/5700", "val": {"id": 5700, "value": 18.1}}
            data_observed = json.loads(event.data)

            try:
                topic_key = data_observed['res']
                kafka_topic = kafka_observe_topics.get(topic_key)
                kafka_producer.send(kafka_topic, data_observed['val'])
            except:
                # in case there is any random observation with no topic associated, we delete it
                delete_observation(
                    device_data['ip'],
                    device_data['port'],
                    data_observed['ep'],
                    data_observed['res'],
                    kafka_producer
                )


def read(device_ip, device_port, endpoint_name, accessing, kafka_topic, kafka_producer):
    '''
    This method will read the value of a desired resource and return its value.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)

    If resource not found or Device not found either, it returns {success: False, message: messageError}

    '''

    url = 'http://{}:{}/api/clients/{}{}?format=JSON'.format(device_ip, device_port, endpoint_name, accessing)
    request = requests.get(url=url)
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing READ operation."+url})

    if request.status_code == 200:
        data = json.loads(request.text)

        if data["success"]:
            # send this data to the final application
            data_to_send = {'data': data['content']['value']}
        else:
            # send fail to kafka topic
            data_to_send = {'success': False}
    else:
        # send fail to kafka topic
        data_to_send = {'success': False}

    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Status code: {} | Sending read data.".format(request.status_code)})

    kafka_producer.send(kafka_topic, data_to_send)


def write(device_ip, device_port, endpoint_name, accessing, data, kafka_producer):
    '''
    This method will try to write the passed values into a desired resource and return True if Success or False otherwise.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)

    Data format example: {'id': '0', 'resources': [{'id': "5700", 'value': "5"}]}

    '''
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing WRITE operation."})

    url = 'http://{}:{}/api/clients/{}{}?format=JSON'.format(device_ip, device_port, endpoint_name, accessing)

    # json will set content-type to "application/json", otherwise it fails
    response = requests.put(url=url, json=data)

    success = True
    if response.status_code == 200:
        success = success and json.load(response.text)['success']

    return success


def execute(device_ip, device_port, endpoint_name, accessing, kafka_producer):
    '''
    This method will make the operation EXECUTE of the desired resource and return its code status or error in case of fail.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)
    '''
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing EXECUTE operation."})

    url = 'http://{}:{}/api/clients/{}{}'.format(device_ip, device_port, endpoint_name, accessing)
    response = requests.post(url=url)
    success = True

    if response.status_code == 200:
        success = success and json.load(response.text)['success']

    return success


def observe(device_ip, device_port, endpoint_name, accessing, kafka_topic, kafka_producer):
    '''Given the following Resource data, this method starts the observation of its value'''
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing OBSERVE operation."})

    # we add the new topic to the observe topics
    kafka_observe_topics[accessing] = kafka_topic

    url = 'http://{}:{}/api/clients/{}{}/observe?format=JSON'.format(device_ip, device_port, endpoint_name, accessing)
    requests.post(url=url)


def delete_observation(device_ip, device_port, endpoint_name, accessing, kafka_producer):
    """This method stops an observation when it's required"""
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing DELETE_OBSERVATION operation."})
    url = 'http://{}:{}/api/clients/{}{}/observe'.format(device_ip, device_port, endpoint_name, accessing)
    requests.delete(url=url)


def delete(device_ip, device_port, endpoint_name, accessing, kafka_producer):
    """This method deletes a specific resource"""
    kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Performing DELETE operation."})
    url = 'http://{}:{}/api/clients/{}{}'.format(device_ip, device_port, endpoint_name, accessing)
    requests.delete(url=url)

# ---------------------------SOME AUX LOCAL METHODS-----------------------


def read_and_execute_action_from_buffer(sh_semaphore, sh_buffer, device_data, kafka_producer):
    acquired = sh_semaphore.acquire(blocking=False)  # we do not want the monitor to get blocked

    if acquired:
        message = sh_buffer.pop()
        """
        message_example = {
                        'application': request.POST['app_name'],
                        'iot_connector': data['id_iotconnector'],
                        'shadow': data['shadow_id'],
                        'endpoint': data['id_endpoint'],
                        'resource': data['id_resource'],
                        'accessing': request.POST['resource_accessing'],
                        'operation': request.POST['operation'],
                        'kafka_topic': new_topic_name
                    }
        """

        sh_semaphore.release()

        if message['operation'] == 'OBSERVE':
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read OBSERVE operation."})
            accessing = message['resource_accessing']
            observe(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                accessing,
                message["kafka_topic"],
                kafka_producer  # for debugging
            )

        elif message['operation'] == 'READ':
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read READ operation."})
            read(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                message['resource_accessing'],
                message['kafka_topic'],
                kafka_producer
            )

        elif message['operation'] == 'WRITE':
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read WRITE operation."})
            write(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                message['resource_accessing'],
                message['data'],
                kafka_producer  # FOR DEBUGGING
            )

        elif message['operation'] == 'EXECUTE':
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read EXECUTE operation."})
            execute(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                message['resource_accessing'],
                kafka_producer  # FOR DEBUGGING
            )

        elif message['operation'] == 'DELETE':
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read DELETE operation."})
            delete(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                message['resource_accessing'],
                kafka_producer  # FOR DEBUGGING
            )

        elif message['operation'] == 'DELETE_OBSERVATION':  # Modify later
            kafka_producer.send("LogTopic", {"[Leshan Monitor]": "Read DELETE_OBSERVATION operation."})
            delete_observation(
                device_data['ip'],
                device_data['port'],
                message['endpoint_name'],
                message['resource_accessing'],
                kafka_producer  # FOR DEBUGGING
            )
        else:
            raise IndexError("Operation not valid.")
