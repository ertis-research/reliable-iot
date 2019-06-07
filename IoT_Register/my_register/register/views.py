from . import auxiliar_methods
from http import HTTPStatus
from django import http

import docker
import json


def register(request):
    '''
    Given a dict of data through the request body representing a real device, this endpoint stores this data in the
    database, then tries to deploy a new IoT Connector that does the monitoring work for that device.

    Data example:
    {
    'type': 'Leshan / MQTT / CoAP',
    'ip': '<some valid ip>',
    'port': '<some valid port>',
    'token': '<some valid token string>',
    'MAC' : <device's mac direction>,
    'shadow_id': <some_valid_shadow_id>
    }

    :param request: HttpRequest
    :return: dict
    '''

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # we will use this token
        if auxiliar_methods.check_token_validation(token):

            # getting the information to store
            device_data_to_store = auxiliar_methods.extract_request_data(request)
            # sending the store request to the DB Api
            store_response = auxiliar_methods.register_store_request(device_data_to_store, token)

            if store_response['status_code'] == 200:
                device_info = json.loads(store_response['message'])

                # run a new image of Docker Monitor on the new device
                docker_client = docker.from_env()
                docker_environment_variables = [
                    'IOT_CONNECTOR_ID={}'.format(device_info['_id']),
                    'IOT_DEVICE_TOKEN={}'.format(token),
                    'SHADOW_ID={}'.format(device_data_to_store['Shadow_id'])
                ]

                networks = ['IOT_default']

                image, status_code, message = \
                    auxiliar_methods.get_docker_image(token, device_info['type'])

                if status_code == 200:
                    try:
                        # it returns the created service
                        # in case of fail Raises: docker.errors.APIError
                        service = docker_client.services.create(image=image, env=docker_environment_variables,
                                                                networks=networks, mounts=['/dev/log:/dev/log:rw'])
                    except:
                        service = None
                        message = 'Failed to deploy dinamically.'

                else:
                    service = None
                    message = 'Docker image doesn\'t exist.'

                # if running a container fails (delete data from db)
                if not service:
                    auxiliar_methods.delete_real_device(device_info['_id'], token)
                    status_code_to_send = HTTPStatus.INTERNAL_SERVER_ERROR
                    info_to_send = {'message': 'Monitoring could not be deployed. '+message}
                else:
                    status_code_to_send = 200
                    info_to_send = {'device_id': device_info['_id'], 'service_id': service.id}

            else:
                status_code_to_send = store_response['status_code']  # we return the DB status code & message in case of fail
                info_to_send = {'message': store_response['message'] + '. Virtual device could not be created.'}

            return http.JsonResponse(data=info_to_send, status=status_code_to_send)
        else:
            return http.JsonResponse(data={'message': "Invalid Credentials. FORBIDDEN"}, status=HTTPStatus.FORBIDDEN)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)
