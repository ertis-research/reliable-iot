import json
import uuid

from my_db.restful_API.auth import core
from my_db.db_mongo import mongo_setup
from my_db.db_mongo.model import Token
from my_db.db_mongo.model import UserData
from my_db.db_mongo.model import Shadow
from http import HTTPStatus
from django import http
mongo_setup.global_init()  # makes connection with db


def create_shadow(request):  # check token if valid later
    '''
    This endpoint expects a dict passed in the body with the following fields:
    {
    name : text:String,
    description: text:String
    }

    With this information it store in the database a new Shadow Device.
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):

            if request.POST:
                try:
                    # STORE TOKEN IN DATA BASE
                    db_shdw = Shadow()
                    db_shdw._id = uuid.uuid4().__str__()
                    db_shdw.description = request.POST['description']
                    db_shdw.name = request.POST['name']
                    db_shdw.save()

                    return http.JsonResponse(data={'shadow': db_shdw.to_json()}, status=HTTPStatus.OK)
                except:
                    return http.HttpResponse(content=json.dumps({'message': 'Shadow couldn\'t be created'}),
                                             status=HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                return http.HttpResponse(content=json.dumps({'message': 'Try making a post request instead.'}),
                                         status=HTTPStatus.BAD_REQUEST)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_shadow_by_id(request, shdw_id):
    '''
    Given a shadow device id, this method fetches the shadow device from the db and returns it.
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects.with_id(shdw_id)
            if shadow:
                shadow = shadow.to_json()  # json as string
                status = HTTPStatus.OK
            else:
                status = HTTPStatus.NOT_FOUND
                shadow = None

            return http.JsonResponse({'shadow': shadow}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_shadows_by_user_id(request, user_id):  # check token if valid later
    '''
    Given an user id, this method searches for it's shadow devices in the database
    :param request:
    :param user_id:
    :return: JSON shadow list
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            usr = UserData.objects.with_id(user_id)
            if usr:
                shadow_ref_list = usr.shadow  #this returns a list of Shadow Objects
                shadow_list = []
                status = HTTPStatus.OK

                for shdw in shadow_ref_list:
                    shadow_list.append(shdw.to_json())

            else:
                shadow_list = []
                status = HTTPStatus.NOT_FOUND
            return http.JsonResponse({'shadows': shadow_list}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def update_shadow(request, shdw_id):
    '''Given a Shadow id, this method performs the update of the database object related to the id.'''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            data = request.POST
            shadow = Shadow.objects.with_id(shdw_id)  # it gives back a QuerySet

            if shadow:  # if any endpoint fetched
                if 'name' in data:
                    shadow.name = data['name']

                if 'description' in data:
                    shadow.description = data['description']

                if 'token' in data:
                    associated_token = Token.objects.with_id(data['token'])
                    associated_token.save()
                    shadow.tokens.append(associated_token.to_dbref())  # append token ref

                try:
                    shadow.save()
                    code_to_return = HTTPStatus.OK
                    data_to_return = {'message': 'Success'}
                except:
                    return http.HttpResponseServerError(content=json.dumps({'message': 'Error Updating'}), status=HTTPStatus.INTERNAL_SERVER_ERROR)

            else:  # it theres no shadow
                data_to_return = {'message': 'NOT MODIFIED'}
                code_to_return = HTTPStatus.NOT_MODIFIED

            return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def delete_shadow(request, shdw_id):
    '''
    This Method deletes a the shadow device related to the id given and also REVOKES the token, not remove
        It also ensures Database consistency updating User shadow field by removing itself from it.
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects.with_id(shdw_id)

            if shadow:
                shadow_tokens = shadow.tokens

                # Before we delete the shadow device we revoke all its tokens
                for tk in shadow_tokens:
                    tk.revoked = True
                    tk.save()

                user = UserData.objects(shadow=shdw_id)
                if user:
                    user.update(pull__shadow=shadow)

                try:
                    shadow.delete()
                    code_to_return = HTTPStatus.OK
                    data_to_return = {'message': 'Success'}
                except:
                    return http.HttpResponseServerError(content=json.dumps({'message': 'Error Deleting'}), status=HTTPStatus.INTERNAL_SERVER_ERROR)

            else:  # it theres no shadow
                data_to_return = {'message': 'NOT MODIFIED'}
                code_to_return = HTTPStatus.NOT_MODIFIED

            return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def get_shadow_tokens(request, shdw_id):
    '''
    Given a shadow device id, this method fetches the shadow's tokens from the db and returns them in a list.
    :param request: HttpRequest
    :param shdw_id: String
    :return: tokens: Json
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects.with_id(shdw_id)
            if shadow:
                tokens = shadow.tokens
                tk_list = []

                for tk in tokens:
                    tk_list.append(tk.to_json())

                status = HTTPStatus.OK
            else:
                status = HTTPStatus.NOT_FOUND
                tk_list = None

            return http.JsonResponse({'tokens': tk_list}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_shadow_devices(request, shdw_id):
    '''
    Given a shadow id, this method fetches the devices from the db and returns them in a list.
    :param request: HttpRequest
    :param shdw_id: String
    :return: tokens: Json
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects.with_id(shdw_id)
            if shadow:
                devices = shadow.devices
                devices_list = []
                for dev in devices:
                    devices_list.append(dev.to_json())

                status = HTTPStatus.OK
            else:
                status = HTTPStatus.NOT_FOUND
                devices_list = None

            return http.JsonResponse(data={'devices': devices_list}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)

