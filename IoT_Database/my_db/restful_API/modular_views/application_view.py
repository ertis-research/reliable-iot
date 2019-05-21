from my_db.db_mongo.model import Application
from my_db.restful_API.auth import core
from my_db.db_mongo import mongo_setup
from http import HTTPStatus
from django import http
import uuid
import json

mongo_setup.global_init()  # makes connection with db


def get_all(request):
    """This method returns all Applications from the database"""

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):
            apps = Application.objects()
            apps_list = []

            for app in apps:
                apps_list.append(app.to_json())

            return http.JsonResponse(data={'apps': apps_list}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def store_or_update_app(request, name):
    '''
    Given an App name, this method performs the update of the database object related to the id.

    Type of message in the request body:
    {
        "interest" : "an interest"  # (not a list)
    }

    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            data = request.POST
            app = Application.objects(name=name)  # it gives back a QuerySet

            if app.count():  # if any app fetched, we update it
                app = app.first()

                if 'interest' in data:
                    app.interests.append(data["interest"])

                try:
                    app.save()
                    code_to_return = HTTPStatus.OK
                    data_to_return = {'message': 'Success'}
                except:
                    return http.HttpResponseServerError(content=json.dumps({'message': 'Error Updating'}),
                                                        status=HTTPStatus.INTERNAL_SERVER_ERROR)

            else:  # we store it instead
                new_app = Application()
                new_app._id = uuid.uuid4().__str__()
                new_app.name = name
                if 'interest' in data:
                    new_app.interests.append(data["interest"])

                new_app.save()

                data_to_return = {'message': 'App Stored'}
                code_to_return = HTTPStatus.OK

            return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)

    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def delete_app(request, name):
    '''
    This Method deletes a the shadow device related to the name given
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if core.validate(token):
            app = Application.objects(name=name)

            if app.count():
                app = app.first()
                try:
                    app.delete()
                    code_to_return = HTTPStatus.OK
                    data_to_return = {'message': 'Success'}
                except:
                    return http.HttpResponseServerError(content=json.dumps({'message': 'Error Deleting'}),
                                                        status=HTTPStatus.INTERNAL_SERVER_ERROR)
            else:  # it there's no app
                data_to_return = {'message': 'NOT MODIFIED'}
                code_to_return = HTTPStatus.NOT_MODIFIED

            return http.HttpResponse(content=json.dumps(data_to_return), status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)
