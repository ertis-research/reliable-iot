import json
import uuid

from my_db.restful_API.auth.core import validate, generate, revoke
from my_db.db_mongo import mongo_setup
from my_db.db_mongo.model import Token
from my_db.db_mongo.model import UserData
from my_db.db_mongo.model import Shadow
from my_db.restful_API.auth import core
from http import HTTPStatus
from django import http
mongo_setup.global_init()  # makes connection with db


def generate_token(request):
    '''
    This endpoint expects a dict passed in the body with the following fields:
    {
    type : 'USER / COMPONENT / DEVICE',
    email: (in case of USER type)

    }
    :param request:HttpRequest
    :return: token:json
    '''

    if request.POST:
        token_info = {}
        for key in request.POST:
            token_info[key] = request.POST[key]

        try:
            token = generate(token_info)

            return http.JsonResponse(data={'token': token}, status=HTTPStatus.OK)
        except:
            return http.HttpResponse(content=json.dumps({'message': 'Token couldn\'t be created'}),
                                     status=HTTPStatus.INTERNAL_SERVER_ERROR)
    else:
        return http.HttpResponse(content=json.dumps({'message': 'Try making a post request instead.'}),
                                 status=HTTPStatus.BAD_REQUEST)


def get_token_by_id(request, token_id):
    '''
    Given a token_id, this method fetches the token from the db and returns it.
    :param request: HttpRequest
    :param token_id: String
    :return: token:String
    '''

    # if request.META.get('HTTP_AUTHORIZATION'):
    #     token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
    #     if core.validate(token):

    token_object = Token.objects.with_id(token_id)
    if token_object:
        token = token_object.token
        status = HTTPStatus.OK
    else:
        status = HTTPStatus.NOT_FOUND
        token = None

    return http.JsonResponse(data={'token': token}, status=status)

    #     else:
    #         return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    # else:
    #     return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_tokens_by_user_id(request, user_id):  # this will validate a token (gets it from header)
    '''
    Given an user id this method searches for it's token in the database
    :param request:HttpRequest
    :param user_id: String
    :return: token:Json
    '''
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            user = UserData.objects(_id=user_id)
            if user.count():
                user = user.first()
                token_ref = user.token
                token = Token.objects(_id=token_ref).first()
                token = token.token

                status = HTTPStatus.OK
            else:
                token = None
                status = HTTPStatus.NOT_FOUND
            return http.JsonResponse({'token': token}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_tokens_by_shadow(request, shadow_id):
    '''
    Given a shadow id, this method searches for it's tokens in the database
    :param request:
    :param shadow_id:
    :return: JSON token list
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            shadow = Shadow.objects(_id=shadow_id)
            if shadow.count():
                shadow = shadow.first()
                token_ids_list = shadow.tokens
                token_list = []
                status = HTTPStatus.OK

                for tok in token_ids_list:
                    token_list.append(tok._id)
            else:
                token_list = []
                status = HTTPStatus.NOT_FOUND
            return http.JsonResponse({'tokens': token_list}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def revoke_token(request):  # TOKEN WILL BE PASSED IN THE HEADER
    """This method gets the token from the header and revokes it"""

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        revoke(token)
        return http.JsonResponse(status=HTTPStatus.OK, data={'message': 'success'})
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def validate_token(request):  # TOKEN WILL BE PASSED IN THE HEADER
    """This method gets the token from the header and checks if it's valid or not """

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if validate(token):
            return http.JsonResponse(status=HTTPStatus.OK, data={'message': 'Valid'})
        else:
            revoke(token)  # to ensure that expired tokens are revoked in DB
            return http.JsonResponse(status=HTTPStatus.UNAUTHORIZED, data={"message": 'No valid'})
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)
