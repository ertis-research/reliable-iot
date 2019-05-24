from my_db.db_mongo.model import Endpoint, Resource, IotConnector, Shadow, ResourceUse
from my_db.db_mongo import mongo_setup
from my_db.restful_API.auth import core
from http import HTTPStatus
from django import http

import uuid
mongo_setup.global_init()  # makes connection with db


def get_resource(request, res_id):
    """
    Given a Resource id, this method fetches the related Resource from the Database.

    """
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            resource = Resource.objects.with_id(res_id)
            if resource:
                return http.JsonResponse(data={'data': resource.to_json()}, status=200)
            else:
                return http.JsonResponse(data={'data': 'Not found.'}, status=HTTPStatus.NOT_FOUND)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_similar_resource(request):
    """
    Given info through the data body, this method tries to look for a similar resource as indicated.
    Body data example:
    {
        "resource_code" : <a numeric code> (mandatory | e.g. 5700)
        "shadow_id" : <shadow_id> (optional)
    }

    """
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):

            if 'resource_code' in request.POST:
                data_to_return = {'success': False}
                code_to_return = HTTPStatus.NOT_FOUND

                if 'shadow_id' in request.POST:  # we search only in this shadow
                    shadow = Shadow.objects.with_id(request.POST['shadow_id'])
                    if shadow:
                        data_result, \
                            code_to_return \
                            = search_res_in_shadow(shadow, int(request.POST['resource_code']))

                        data_to_return.update(data_result)

                    else:  # shadow doesn't exist
                        return http.JsonResponse(data={'message': 'Shadow does not exist.'},
                                                 status=HTTPStatus.BAD_REQUEST)

                else:  # We search in every shadow
                    shadows = Shadow.objects()
                    for shadow in shadows:
                        data_result, \
                            code_to_return \
                            = search_res_in_shadow(shadow, int(request.POST['resource_code']))

                        if data_result["success"]:  # if true means it's been found
                            data_to_return.update(data_result)
                            break

                return http.JsonResponse(data=data_to_return, status=code_to_return)
            else:
                return http.JsonResponse(data={'message': 'Resource code not passed.'}, status=HTTPStatus.BAD_REQUEST)

        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def store_resource(request):
    '''This method stores a resource in the database.
        Message to send in the body request:
        {
            'type': String,
            'accessing': String
        }
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):

            new_resource = Resource()
            new_resource._id = uuid.uuid4().__str__()
            new_resource.type = request.POST['type']
            new_resource.accessing = request.POST['accessing']

            try:
                new_resource.save()
                status_to_return = HTTPStatus.OK
                data = {'resource_id': new_resource.pk}
            except:  # Data-Wrong or Connection Failed
                return http.JsonResponse({'message': 'Wrong data format'}, status=HTTPStatus.BAD_REQUEST)

            return http.JsonResponse(data=data, status=status_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def update_resource(request, endpoint_id):
    '''Given an endpoint id, this method updates all the resources' status related to it'''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            data = request.POST
            associated_endpoint = Endpoint.objects.with_id(endpoint_id)  # it could be None (if it's not in the db)

            if associated_endpoint:
                resources_list = associated_endpoint.resources

                for r in resources_list:
                    if 'status' in data:
                        r.status = bool(int(data['status']))
                        r.save()

                data_to_return = {'message': 'Success!'}
                code_to_return = HTTPStatus.OK
            else:
                data_to_return = {'message': 'The id provided doesn\'t exist'}
                code_to_return = HTTPStatus.BAD_REQUEST

            return http.JsonResponse(data=data_to_return, status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def delete_resource(request, res_id):
    '''
    This Method deletes a the Resource related to the id given.
    It also ensures Database consistency updating Endpoint resources field by removing itself from it.
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]

        if core.validate(token):
            resource = Resource.objects.with_id(res_id)
            if resource:

                endpoint = Endpoint.objects(resources=res_id)
                if endpoint:
                    endpoint.update(pull__resources=resource)

                resource.delete()
                data = {"message": 'Success!'}
                sts = HTTPStatus.OK

            else:
                data = {'data': HTTPStatus.NOT_FOUND.name}
                sts = HTTPStatus.NOT_FOUND

            return http.JsonResponse(data=data, status=sts)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def resource_status(request, res_id):
    '''Given a resource id this method returns USING / DOWN / NOT_USING depending on it's status
        If not available -> DOWN
        If it's being used -> USING
        If it's not being used -> NOT_USING
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            resource = Resource.objects.with_id(res_id)

            if resource:
                if resource.status:
                    data = {'status': 'NOT_USING'}
                    if ResourceUse.objects(resource=resource._id).count():
                        data = {'status': 'USING'}
                else:
                    data = {'status': 'DOWN'}

                sts = HTTPStatus.OK
            else:
                sts = HTTPStatus.BAD_REQUEST
                data = {'message': 'Resource not found'}

            return http.JsonResponse(data=data, status=sts)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                     status=HTTPStatus.BAD_REQUEST)


def get_shadow_resources(request, shdw_id):
    '''
    Given a shadow id, this method fetches the token from the db and returns it.
    :param request: HttpRequest
    :param shdw_id: String
    :return: tokens: Json
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects.with_id(shdw_id)
            res_list = []

            if shadow:
                shdw_devices = shadow.devices

                for device in shdw_devices:  # iterator over devices
                    dev_endpoints = device.endpoints

                    for endpoint in dev_endpoints:  # iterator over endpoints
                        resources = endpoint.resources
                        for res in resources:  # iterator over resources
                            res_list.append(res.to_json())

            return http.JsonResponse(data={'resources': res_list}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'},
                                     status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def get_device_resources(request, dev_id):
    '''
    Given a device id, this method fetches the token from the db and returns it.
    :param request: HttpRequest
    :param dev_id: String
    :return: tokens: Json
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            device = IotConnector.objects.with_id(dev_id)
            res_list = []

            if device:
                dev_endpoints = device.endpoints

                for endpoint in dev_endpoints:  # iterator over endpoints
                    resources = endpoint.resources
                    for res in resources:  # iterator over resources
                        res_list.append(res.to_json())

            return http.JsonResponse(data={'resources': res_list}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'},
                                     status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


# -----------------------------SOME AUXILIAR METHODS---------------------------------------


def search_res_in_shadow(shadow, res_type):
    '''
    if found update success to true and 0K status code,
    otherwise, false and Not Found.
    '''

    data_to_return = {'success': False}
    code_to_return = HTTPStatus.NOT_FOUND

    for device in shadow.devices:  # iretating over Iot_Connectors
        endpoint_list = device.endpoints

        for endpoint in endpoint_list:  # iterating over Endpoints
            resources_list = endpoint.resources

            for resource in resources_list:  # iterating over Resource
                if resource.type == res_type and resource.status:
                    data_to_return.update({"success": True, 'id_iotconnector': device._id, 'id_endpoint': endpoint._id})
                    code_to_return = HTTPStatus.OK
                    return data_to_return, code_to_return

    return data_to_return, code_to_return  # if this point is reached it means resource was not found
