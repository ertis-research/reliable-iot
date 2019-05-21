from my_db.db_mongo.model import IotConnector, Token, Endpoint, Shadow, ResourceUse
from my_db.db_mongo import mongo_setup
from my_db.restful_API.auth import core
from http import HTTPStatus
from django import http

import json
import uuid

mongo_setup.global_init()  # makes connection with db


def get_physical_device(request, dev_id):
    """
    Given a Device id, this method fetches the related Device from the Database.
    """
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            device = IotConnector.objects.with_id(dev_id)
            if device:

                return http.JsonResponse(data={'message': device.to_json()}, status=200)
            else:
                return http.JsonResponse(data={'message': 'No device found'}, status=404)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def device_status(request, dev_id):
    '''Given a device id this method returns USING / DOWN / NOT_USING depending on it's endpoints and resources status
        If all resources are down -> DOWN
        If any resource is being used -> USING
        If no resource is being used -> NOT_USING
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            device = IotConnector.objects.with_id(dev_id)

            if device:

                # Here i got all the available endpoints of the device
                up_endpoints_list = [endpoint for endpoint in device.endpoints if endpoint.available]

                if up_endpoints_list:
                    resources_list = []
                    for endpoint in up_endpoints_list:
                        resources_list.extend(endpoint.resources)

                    data = {'status': 'NOT_USING'}

                    for resource in resources_list:
                        if ResourceUse.objects(resource=resource._id).count():
                            data = {'status': 'USING'}
                            break

                else:
                    data = {'status': 'DOWN'}

                sts = HTTPStatus.OK
            else:
                sts = HTTPStatus.BAD_REQUEST
                data = {'message': 'Device not found'}

            return http.JsonResponse(data=data, status=sts)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                     status=HTTPStatus.BAD_REQUEST)


def register_device(request):
    '''
    This method receives a registration message and stores in the database the information that has been passed to it.
    The received data represents a real device.

    Registration message: ¡¡¡ All data is mandatory !!! (otherwise a fail will occur)
    {
        'Name' : 'device name'
        'Type': '.....',
        'Port': '.....',
        'Ip': '.....',
        'Mac': '.....',
        'Shadow_id': '.....',
    }
    :param request:
    :return:
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            # getting all data from request
            iot_device_info = request.POST
            new_real_device = IotConnector()

            new_real_device._id  = uuid.uuid4().__str__()
            new_real_device.type = iot_device_info['Type']
            new_real_device.port = iot_device_info['Port']
            new_real_device.ip   = iot_device_info['Ip']
            new_real_device.mac  = iot_device_info['Mac']

            # Check if another device has been registered with the same Mac direction
            if not IotConnector.objects(mac=iot_device_info['Mac']).count():

                ref_token = Token.objects(token=iot_device_info['Token'])
                if ref_token.count():
                    ref_token = ref_token.first()
                    ref_token.save()
                    new_real_device.token = ref_token.to_dbref()

                    new_real_device.save()

                    # HERE WE UPDATE THE SHADOW DEVICE THAT HOSTS THIS REAL DEVICE
                    sh_device = Shadow.objects.with_id(iot_device_info['Shadow_id'])

                    if sh_device:
                        sh_device.devices.append(new_real_device.to_dbref())
                        sh_device.save()

                        status_to_return = HTTPStatus.OK
                        data = {'message': new_real_device.to_json()}
                    else:
                        data = {'message': 'There is no shadow device to reference with that id.'}
                        status_to_return = HTTPStatus.BAD_REQUEST
                else:
                    data = {'message': 'Token passed could not be referenced.'}
                    status_to_return = HTTPStatus.BAD_REQUEST

            else:  # it means a device with same mac has been registered
                status_to_return = HTTPStatus.BAD_REQUEST
                data = {'message': 'This device was already registered in the system.'}

            return http.JsonResponse(data=data, status=status_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def update_device(request, dev_id):
    """
    Given a Device id, this method performs the update of the database object related to the id.
    """
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            device = IotConnector.objects.with_id(dev_id)
            if device:
                data = request.POST

                if 'ip' in data:
                    device.update(set__ip=data['ip'])
                if 'port' in data:
                    device.update(set__port=data['port'])
                if 'token' in data:
                    ref_token = Token.objects(token=data['token'])
                    if ref_token.count():
                        ref_token = ref_token.first()
                        ref_token.save()
                        device.update(set__token=ref_token.to_dbref())

                if 'mac' in data:
                    device.update(set__mac=data['mac'])

                if 'type' in data:
                    device.update(set__type=data['type'])

                code_to_return = HTTPStatus.OK
                data_to_return = {'message': 'Success'}

                if 'endpoints' in data:
                    for ep in json.loads(data['endpoints']):  # data['endpoints'] = '[epID, ...]' (json.dumps([epID, ...]))
                        associated_ep = Endpoint.objects.with_id(ep)
                        associated_ep.save()
                        device.endpoints.append(associated_ep.to_dbref())  # append endpoint ref

                    try:
                        device.save()
                        code_to_return = HTTPStatus.OK
                        data_to_return = {'message': 'Success'}
                    except:
                        code_to_return = HTTPStatus.INTERNAL_SERVER_ERROR
                        data_to_return = {'message': 'Failed to update physical device'}

                return http.JsonResponse(data=data_to_return, status=code_to_return)
            else:
                return http.JsonResponse(data={'message': 'No device found to update'}, status=404)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def delete_device(request, dev_id):
    '''
    It performs cascade delete from device to it's resources and also REVOKES the token, not remove.
    It also ensures Database consistency updating Shadow devices field by removing itself from it.
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            device = IotConnector.objects.with_id(dev_id)

            if device:
                # we revoke his token
                device.token.revoked = True
                device.token.save()

                shadow = Shadow.objects(devices=dev_id)
                if shadow:
                    shadow.update(pull__devices=device)  # ensure DB consistency

                # we delete his endpoints
                endpoints = device.endpoints
                for ep in endpoints:
                    resources = ep.resources

                    # we delete all the resources of the endpoint
                    for res in resources:
                        res.delete()

                    ep.delete()

                # we delete the device at last
                device.delete()

                return http.JsonResponse(status=200, data={'message': 'Success'})
            else:
                return http.JsonResponse(data={'message': 'Could not remove device.'}, status=HTTPStatus.NOT_MODIFIED)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)

