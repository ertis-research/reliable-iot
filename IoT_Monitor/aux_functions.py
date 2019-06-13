import requests
import json

ACCEPTED_TAGS = ['endpoint', 'registrationId', 'registrationDate', 'lastUpdate', 'address', 'lifetime']
db_url = 'http://mongoapi:80/'


def get_real_device(dev_id, token):
    '''
    Given a Real Device Id, this method performs a request to the Database API in order to fetch an Real Device
    '''

    url = db_url + 'getPhysicalDevice/{}/'.format(dev_id)
    headers = {'Authorization': 'Token {}'.format(token)}
    r = requests.get(url=url, headers=headers)

    if r.status_code == 200:
        x = json.loads(r.text)  # {'message': '{...}'}
        return json.loads(x['message'])  # this will return a json object {'_id': '...', ...}
    else:
        return {}


def purge_update_data(json_string):
    '''
    Takes an update Json String, converts it to Json Object and takes the essential data needed to store in the DB

    '''

    x = json.loads(json_string)
    ret = {}

    for k, v in x.items():
        if k in ACCEPTED_TAGS:
            ret[k] = v

    return ret


def get_leshan_resources_data(resources_list):
    '''
        Given a resource list, the basic data is returned in a list of Json objects ([{'accessing': '/1/0', 'type': '1'}, {...}, ...])
    (Resource list: e.g. [{"url":"/","attributes":{"rt":"oma.lwm2m"}},{"url":"/1/0","attributes":{}},{"url":"/3/0","attributes":{}}, {...}, ...])

    '''

    return_data = []

    for y in resources_list:
        resource = {}
        resource['accessing'] = y['url']

        typee = y['url'].split('/')[1]  # "/" => ['','']  #  "/1/0" => ['', '1', '0']
        if typee != '':
            resource['type'] = typee
            return_data.append(resource)

    return return_data


def get_ep_register_data(endpoint):
    '''
    Given an endpoint, it's essential data is returned in order to be stored in the DB

    '''

    ep_store_data = {
        'registrationId': endpoint['registrationId'],
        'address': endpoint['address'],
        'name': endpoint['endpoint']
    }

    return ep_store_data


def ep_store_request(data, token):
    '''
    Performs a request to the Database API in order to store an Endpoint

    '''

    headers = {'Authorization': 'Token {}'.format(token)}
    store_url = db_url + 'storeEndpoint/'
    response = requests.post(url=store_url, data=data, headers=headers)
    ep_id = json.loads(response.text)['endpoint_id']

    return ep_id


def ep_get_request(leshan_id, token):
    '''
    Performs a request to the Database API in order to store an Endpoint

    '''

    headers = {'Authorization': 'Token {}'.format(token)}
    store_url = db_url + 'getEndpointByLeshanId/{}/'.format(leshan_id)
    response = requests.get(url=store_url, headers=headers)
    ep_id = json.loads(response.text)['endpoint_id']

    return ep_id


def res_store_request(data, token):
    '''
    Performs a request to the Database API in order to store a Resource
    '''

    headers = {'Authorization': 'Token {}'.format(token)}
    store_url = db_url + 'storeResource/'
    response = requests.post(url=store_url, data=data, headers=headers)
    res_id = json.loads(response.text)['resource_id']

    return res_id


def store_endpoints_and_resources(endpoint_list, device_id, token):
    '''
     Given an endpoint LIST, it's data and resources are stored in the DB

    (example :[
    {
        "endpoint":"C2",
        "registrationId":"hyvqs5UDTb",
        "registrationDate":"2019-04-08T20:37:17+02:00",
        "lastUpdate":"2019-04-08T20:37:17+02:00",
        "address":"127.0.0.1:56020","lwM2mVersion":"1.0",
        "lifetime":30,"bindingMode":"U","rootPath":"/",
        "objectLinks":[
            {"url":"/","attributes":{"rt":"oma.lwm2m"}},
            {"url":"/1/0","attributes":{}},
            {"url":"/3/0","attributes":{}},
            {"url":"/6/0","attributes":{}},
            {"url":"/3303/0","attributes":{}}
        ],
        "secure":false,"additionalRegistrationAttributes":{}}
        ]
 )
    '''

    headers = {'Authorization': 'Token {}'.format(token)}
    url_update_device = db_url + 'updatePhysicalDevice/{}/'.format(device_id)

    device_endpoint_ids = []  # for device update

    for endpoint in endpoint_list:
        register_data = get_ep_register_data(endpoint)
        ep_id = ep_store_request(register_data, token)  # STORE ENDPOINT
        device_endpoint_ids.append(ep_id)

        # for every endpoint, we get all his resources' data
        resources_list = get_leshan_resources_data(endpoint['objectLinks'])

        endpoint_resources_ids = []  # for endpoint update
        # we just got a list of resources, let's store each of them and get their id's
        for resource in resources_list:
            res_id = res_store_request(resource, token)  # we store the resource & get id
            endpoint_resources_ids.append(res_id)

        # we update here the endpoint resource's list
        update_endpoint(ep_id, {'resources': json.dumps(endpoint_resources_ids)}, token)

    # we update the device's id list
    requests.post(url=url_update_device,
                  data={'endpoints': json.dumps(device_endpoint_ids)},
                  headers=headers)

    return device_endpoint_ids


def update_endpoint(endpoint_id, data, token):
    '''
    Given an endpoint id some data and a valid token, this method updates the Database
    endpoint and resources (if status is modified)
    '''

    headers = {'Authorization': 'Token {}'.format(token)}
    update_endpoint_url = db_url + 'updateEndpoint/{}/'.format(endpoint_id)
    requests.post(url=update_endpoint_url, data=data, headers=headers)


def get_endpoint_id(leshan_id, token):
    """
    Given a leshan id, this method queries the endpoint and returns the database endpoint _id

    """

    headers = {'Authorization': 'Token {}'.format(token)}
    update_endpoint_url = db_url + 'getEndpointByLeshanId/{}/'.format(leshan_id)
    r = requests.get(url=update_endpoint_url, headers=headers)
    if r.status_code == 200:
        return json.loads(r.text)['endpoint_id']

    return None
