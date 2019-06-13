from .UsefulData import Token, KfkAdminClient, KfkProducer, URL
from kafka.admin import NewTopic
from http import HTTPStatus
from django import http

import requests
import json


def interest(request):
    '''
    An final application will show interest in some resource (it can specify the id of a specific shadow device)
    Message example:
        {
            "app_name": <a name> (mandatory)
            "shadow_id": <an id> (optional),
            "resource_accessing": <...> ( mandatory | e.g. /3303/1/5700 )
            "operation" : <...> (optional | OBSERVE / READ / WRITE / EXECUTE / DELETE / DELETE_OBSERVATION)
        }

    Returns:
        - OK if resource exists & it's available
        - NOT_FOUND if resource does not exist or unavailable
        - BAD_REQUEST if mandatory field misses
    '''

    token = Token.get_instance()

    if request.POST:
        if "resource_accessing" in request.POST and "app_name" in request.POST:
            # We check the availability of the resource
            code_to_return, data = request_similar_resource(token, request.POST)

            # we store the new app or we update
            x = {"resource_accessing": request.POST["resource_accessing"],
                 "operation": request.POST['operation'],
                 "status": code_to_return.name
                 }

            if "shadow_id" in request.POST:
                x['shadow_id'] = request.POST['shadow_id']

            store_or_update_app(token, {"interest": json.dumps(x)}, request.POST['app_name'])

        else:
            code_to_return = HTTPStatus.BAD_REQUEST

        return http.JsonResponse(data={"Message": code_to_return.name}, status=code_to_return)
    else:
        return http.JsonResponse(data={'message': "Try to make a POST request instead."},
                                 status=HTTPStatus.BAD_REQUEST)


def action(request):
    '''
    An final application will ask the system for an specific action (it can specify the id of a specific shadow device)
    Message example:
        {
            "app_name": <a name> (mandatory)
            "shadow_id": <an id> (optional),
            "resource_accessing": <...> ( mandatory | e.g. /3303/1/5700 )
            "operation" : <...> (madatory | OBSERVE / READ / WRITE / EXECUTE / DELETE)
            "data": {} (mandatory for WRITE operation)
        }

    NOTE: This method should be called after having called the interest method and make sure the resource that's being
    requested is available.

    ******THIS METHOD DOES NOT CHECK IF THE INTEREST METHOD WAS CALLED BEFORE********

    Returns:
        - Kafka_topic: <string> 
    '''

    token = Token.get_instance()

    if request.POST:
        if "resource_accessing" in request.POST and "app_name" in request.POST and "operation" in request.POST:
            producer = KfkProducer.get_instance()
            admin = KfkAdminClient.get_instance()

            # check if logic is already created
            if request.POST['operation'] == "OBSERVE":
                code_to_return, data = logic_already_created(token, request.POST)
            else:
                data = {'success': False}

            if not data['success']:  # there is no similar logic created
                producer.send("LogTopic", {"[Iot Shadow Apps]": "Logic not already created"})

                code_to_return, data = request_similar_resource(token, request.POST)
                message = {"Message": code_to_return.name}

                if data['success']:
                    producer.send("LogTopic", {"[Iot Shadow Apps]": "New Logic created"})
                    new_topic_name = data['id_iotconnector'] + request.POST['app_name']

                    # we create a new topic between the final app and the iot connector
                    # topic name will be a combination of Iot_connector id and app name (e.g. "1234finalapp")
                    # if exception occurs it means topic is aleready created between app and monitor
                    # we re-use it
                    try:
                        admin.create_topics([NewTopic(new_topic_name, num_partitions=2, replication_factor=2)])
                    except:
                        pass

                    store_or_update_app(token, {}, request.POST['app_name'])

                    # we store the new usage in the database
                    _data = {
                        'application': request.POST['app_name'],
                        'iot_connector': data['id_iotconnector'],
                        'shadow': data['shadow_id'],
                        'endpoint': data['id_endpoint'],
                        'resource': data['id_resource'],
                        'accessing': request.POST['resource_accessing'],
                        'operation': request.POST['operation'],
                        'kafka_topic': new_topic_name
                    }
                    store_usage_data(token, _data)

                    # We tell the iot connector to do the action asked for
                    iot_connector_data = {'operation': request.POST['operation'],
                                          'resource_accessing': request.POST['resource_accessing'],
                                          'kafka_topic': new_topic_name,
                                          'endpoint_name': data['name_endpoint']
                                          }

                    if "data" in request.POST and request.POST['operation'] == 'WRITE':
                        iot_connector_data['data'] = request.POST['data']

                    producer.send(data['id_iotconnector'], iot_connector_data)

                    message = {"Message": 'Success', "kafka_topic": new_topic_name}
                else:
                    producer.send("LogTopic", {"[Iot Shadow Apps]": "Could not create New Logic"})

            else:  # if similar logic already created we only return the topic to the app
                producer.send("LogTopic", {"[Iot Shadow Apps]": "Logic already created"})

                store_or_update_app(token, {}, request.POST['app_name'])  # we store or update the app
                message = {"Message": 'Success', "kafka_topic": data['kafka_topic']}
                update_usage_data(token, {"application": request.POST['app_name']}, data['_id'])
                code_to_return = 200
        else:
            code_to_return = HTTPStatus.BAD_REQUEST
            message = {"Message": code_to_return.name}

        return http.JsonResponse(data=message, status=code_to_return)
    else:
        return http.JsonResponse(data={'message': "Try to make a POST request instead."},
                                 status=HTTPStatus.BAD_REQUEST)


# ------------------------------------------SOME AUX METHODS--------------------------------------------------------

def request_similar_resource(token, data_):
    """If a similar resource to the data_ passed exists, this method gets and returns it """

    headers = {'Authorization': 'Token {}'.format(token.token)}

    # get the resource endpoint
    url_check_res = URL.DB_URL + 'getSimilarResource/'  # only res code if shadow id not passed
    resource_code = data_['resource_accessing'].split('/')[1]
    url_check_res += '{}/'.format(resource_code)

    if "shadow_id" in data_:
        url_check_res += "{}/".format(data_['shadow_id'])

    req = requests.get(url=url_check_res, headers=headers)

    code_to_return = HTTPStatus.NOT_FOUND
    data_to_return = {"success": False}

    if req.status_code == HTTPStatus.OK:
        code_to_return = HTTPStatus.OK
        data_to_return = json.loads(req.text)

    return code_to_return, data_to_return


def logic_already_created(token, data_):
    """If a logic is already created, this method gets and returns it """

    resource_code = data_['resource_accessing'].split('/')[1]

    headers = {'Authorization': 'Token {}'.format(token.token)}
    url = URL.DB_URL + 'getCreatedLogic/{}/{}/'.format(
        resource_code,
        data_['operation']
    )

    if "shadow_id" in data_:
        url += "{}/".format(
            data_['shadow_id']
        )

    req = requests.get(url=url, headers=headers)

    code_to_return = HTTPStatus.NOT_FOUND
    data_to_return = {"success": False}

    if req.status_code == HTTPStatus.OK:
        code_to_return = HTTPStatus.OK
        data_to_return['success'] = True

        data_to_return.update(json.loads(req.text))  # {'kafka_topic': <topic>, '_id': 'logic_id' }

    return code_to_return, data_to_return


def store_usage_data(token, data_):
    """Performs a request to the database to store a ResourceUse instance"""
    headers = {'Authorization': 'Token {}'.format(token.token)}

    url = URL.DB_URL + 'createUsageResource/'
    requests.post(url=url, data=data_, headers=headers)


def update_usage_data(token, data_, logic_id):
    """Performs a request to the database to update a ResourceUse instance"""
    headers = {'Authorization': 'Token {}'.format(token.token)}

    url = URL.DB_URL + 'updateUsageResource/{}/'.format(logic_id)
    requests.post(url=url, data=data_, headers=headers)


def store_or_update_app(token, data_, appname):
    """Performs a request to the database to store or update an Application"""
    headers = {'Authorization': 'Token {}'.format(token.token)}
    url_store_update = URL.DB_URL + 'storeOrUpdateApp/{}/'.format(appname)
    requests.post(url=url_store_update, data=data_, headers=headers)
