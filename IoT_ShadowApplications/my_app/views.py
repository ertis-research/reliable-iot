from .UsefulData import Token, KfkAdminClient, KfkProducer, URL
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
            "operation" : <...> (optional | OBSERVE / READ / WRITE / EXECUTE)
        }

    Returns:
        - OK if resource exists & it's available
        - NOT_FOUND if resource does not exist or unavailable
        - BAD_REQUEST if mandatory field misses
    '''

    token = Token.get_instance()

    if request.POST:
        if "resource_accessing" in request.POST and "app_name" in request.POST:
            headers = {'Authorization': 'Token {}'.format(token.token)}

            # We check the availability of the resource
            code_to_return, data = request_similar_resource(token, request.POST)

            # we store the new app or we update
            url_store_update = URL.DB_URL + 'storeOrUpdateApp/{}/'.format(request.POST['app_name'])
            x = {"resource_accessing": request.POST["resource_accessing"],
                 "operation": request.POST['operation'],
                 "status": code_to_return.name}

            if "shadow_id" in request.POST:
                x['shadow_id'] = request.POST['shadow_id']
            requests.post(url=url_store_update, data={"interest": json.dumps(x)}, headers=headers)

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
            "operation" : <...> (madatory | OBSERVE / READ / WRITE / EXECUTE)
        }

    NOTE: This method should be called after having called the interest method and make sure the resource that's being
    requested is available.

    ******THIS METHOD DOES NOT CHECK IF THE INTEREST METHOD WAS CALLED BEFORE********

    Returns:
        - Kafka_topic: <string> if
    '''

    token = Token.get_instance()

    if request.POST:
        if "resource_accessing" in request.POST and "app_name" in request.POST and "operation" in request.POST:
            producer = KfkProducer.get_instance()
            admin = KfkAdminClient.get_instance()

            # check if logic is already created
            data, code_to_return = logic_already_created(token, request.POST)

            if not data['success']:  # there is no similar logic created

                code_to_return, data = request_similar_resource(token, request.POST)
                message = {"Message": code_to_return.name}

                if data['success']:
                    new_topic_name = data['id_iotconnector']+request.POST['app_name']

                    # we create a new topic between the final app and the iot connector
                    # topic name will be a combination of Iot_connector id and app name (e.g. "1234finalapp")
                    admin.create_topics([new_topic_name])

                    # We tell the iot connector to do the action asked for

                    iot_connector_data = {'operation': request.POST['operation'],
                                          'resource_accessing': request.POST['resource_accessing'],
                                          'kafka_topic': new_topic_name
                                          }

                    producer.sent(data['id_iotconnector'], iot_connector_data)

                    message = {"Message": 'Success', "kafka_topic": new_topic_name}

            else:  # if similar logic already created we only return the topic to the app
                message = {"Message": 'Success', "kafka_topic": data['kafka_topic']}
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
    url_check_res = URL.DB_URL + 'getSimilarResource/{}/'  # only res code if shadow id not passed
    resource_code = data_['resource_accessing'].split('/')[1]
    url_check_res.format(resource_code)

    if "shadow_id" in data_:
        url_check_res += "{}/".format(data_['shadow_id'])

    req = requests.get(url=url_check_res, headers=headers)

    code_to_return = HTTPStatus.NOT_FOUND
    data_to_return = {}

    if req.status_code == HTTPStatus.OK:
        code_to_return = HTTPStatus.OK
        data_to_return = json.loads(req.text)

    return code_to_return, data_to_return


def logic_already_created(token, data_):
    """If a logic is already created, this method gets and returns it """

    resource_code = data_['resource_accessing'].split('/')[1]

    headers = {'Authorization': 'Token {}'.format(token.token)}
    url = URL.DB_URL + 'getCreatedLogic/{}/{}/{}/'.format(
        data_['shadow_id'],
        resource_code,
        data_['operation']
    )

    req = requests.get(url=url, headers=headers)

    code_to_return = HTTPStatus.NOT_FOUND
    data_to_return = {}

    if req.status_code == HTTPStatus.OK:
        code_to_return = HTTPStatus.OK
        data_to_return = json.loads(req.text)  # {'kafka_topic': <topic> }

    return code_to_return, data_to_return
