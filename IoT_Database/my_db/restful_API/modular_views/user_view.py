from my_db.restful_API.auth import core
from my_db.db_mongo import mongo_setup
from my_db.db_mongo.model import UserData
from my_db.db_mongo.model import Shadow
from http import HTTPStatus
from django import http

import json

mongo_setup.global_init()  # makes connection with db


def update_user(request, usr_id):
    """Given an user id, this method updates the database object of the user."""

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            data = request.POST
            usr_l = UserData.objects(_id=usr_id)  # it gives back a QuerySet

            if usr_l.count():  # if any endpoint fetched
                usr = usr_l.first()
                if 'username' in data:
                    usr.username = data['username']

                if 'shadow' in data:
                    associated_shadow = Shadow.objects.with_id(data['shadow'])  # it could be None (if it's not in the db)
                    associated_shadow.save()  # if i don't do this i can't access to_dbref() in the next line
                    usr.shadow.append(associated_shadow.to_dbref())

                    usr.save()
                    code_to_return = HTTPStatus.OK
                    data_to_return = {'message': 'Success'}

                    return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
            else:  # it theres no shadow
                data_to_return = {'message': 'NOT MODIFIED'}
                code_to_return = HTTPStatus.NOT_MODIFIED
                return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)
