from kafka import KafkaClient, KafkaProducer, KafkaConsumer
import aux_functions
import sseclient  # install sseclient-py library
import requests
import urllib3
import json


def get_data_stream(token, api_endpoint, device_data):
    """ Start REST streaming device events given a Nest token.  """

    kafka_producer = KafkaProducer(bootstrap_servers='kafka:9094',
                                   client_id=device_data['_id'],
                                   value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                   # value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                                   )

    headers = {
        # 'Authorization': "Bearer {0}".format(token),
        'Accept': 'text/event-stream'
    }
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

        if event_type == 'UPDATED':  # updates periodically incoming
            data_to_store = aux_functions.purge_update_data(event.data)
            aux_functions.execute_endpoint_update(data_to_store, token)
            kafka_producer.send('RegisterTopic', {'id_list': [event.data]})

        elif event_type == 'REGISTRATION':
            endpoint = json.loads(event.data)
            endpoints_id_list = aux_functions.store_endpoints_and_resources(endpoint, device_data['_id'], token)

            # inform to recovery shadow at topic RegisterTopic when new endpoints registered in the Iot Connector
            kafka_producer.send('RegisterTopic', {'id_list': endpoints_id_list})

        elif event_type == 'DEREGISTRATION':  # we do not delete the data, we set status to 0, which means, unavailable
            endpoint = json.loads(event.data)
            aux_functions.deregistration_endpoint_and_resources(endpoint['registrationId'], token)

            # inform to recovery shadow when new device has fallen down at topic FailureTopic
            kafka_producer.send('FailureTopic', {'leshan_id': endpoint['registrationId']})

        elif event_type == 'NOTIFICATION':
            endpoint = json.loads(event.data)
            endpoints_id_list = aux_functions.store_endpoints_and_resources(endpoint, device_data['_id'], token)


def read(device_ip, device_port, endpoint_name, accessing, resource_code, kafka_topic, kafka_producer):
    '''
    This method will read the value of a desired resource and return its value.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)

    If resource not found or Device not found either, it returns {success: False, message: messageError}

    '''

    url = 'http://{}:{}/api/clients/{}/{}/{}?format=JSON'
    url.format(device_ip, device_port, endpoint_name, accessing, resource_code)
    request = requests.get(url=url)

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

    kafka_producer.send(kafka_topic, data_to_send)


def write(device_ip, device_port, endpoint_name, accessing, resource_code, data):
    '''
    This method will try to write the passed values into a desired resource and return True if Success or False otherwise.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)

    Data format example: {'id': '0', 'resources': [{'id': "5700", 'value': "5"}]}

    '''

    url = 'http://{}:{}/api/clients/{}/{}/{}?format=JSON'
    url.format(device_ip, device_port, endpoint_name, accessing, resource_code)

    # json will set content-type to "application/json", otherwise it fails
    response = requests.put(url=url, json=data)

    success = True
    if response.status_code == 200:
        success = success and json.load(response.text)['success']

    return success


def execute(device_ip, device_port, endpoint_name, accessing, resource_code_reset):
    '''
    This method will make the operation EXECUTE of the desired resource and return its code status or error in case of fail.
    Resources route are like the following: accessing/code = /3303/0/5601 (accessing= /3303/0, code=5601)
    '''

    url = 'http://{}:{}/api/clients/{}/{}/{}'
    url.format(device_ip, device_port, endpoint_name, accessing, resource_code_reset)
    response = requests.post(url=url)
    success = True

    if response.status_code == 200:
        success = success and json.load(response.text)['success']

    return success


def observe(device_ip, device_port, endpoint_name, accessing, resource_code):
    '''Given the following Resource data, this method starts the observation of its value'''

    url = 'http://{}:{}/api/clients/{}/{}/{}/observe?format=JSON'
    url.format(device_ip, device_port, endpoint_name, accessing, resource_code)
    requests.post(url=url)


def delete(device_ip, device_port, endpoint_name, accessing, resource_code):
    """stops an observation"""
    url = 'http://{}:{}/api/clients/{}/{}/{}/observe'
    url.format(device_ip, device_port, endpoint_name, accessing, resource_code)
    requests.delete(url=url)

