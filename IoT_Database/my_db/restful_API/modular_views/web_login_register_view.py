from my_db.db_mongo import mongo_setup
from my_db.db_mongo.model import Token
from my_db.db_mongo.model import UserData
from my_db.restful_API.auth import core
from http import HTTPStatus
from django import http

import json
import uuid

mongo_setup.global_init()  # makes connection with db


def login(request):
    """
    - When POST is received, it performs user data check & validation
    """
    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        password_hash = core.make_hash(password)  # make password hash

        user_db = UserData.objects(username=email, password=password_hash)

        if user_db.count():  # if true, email and password registered in the system
            usr = user_db.first()
            # WE NEED TO PROVIDE THE USER A NEW FRESH TOKEN
            token = core.generate({'type': 'USER', 'email': request.POST['email']})

            tk_ref = Token.objects.with_id(token)
            tk_ref.save()

            usr.token = tk_ref.to_dbref()
            usr.save()  # update user's token with the new one

            data = {'id': usr._id, 'token': tk_ref.token, 'email': request.POST['email']}
            return http.JsonResponse(data=data, status=HTTPStatus.OK)
        else:
            return http.HttpResponse(content=json.dumps({'message': 'Wrong Password or Email'}),
                                     status=HTTPStatus.NOT_FOUND)

    else:
        return http.HttpResponse(content=json.dumps({'message': 'Try making a post request instead.'}),
                                 status=HTTPStatus.BAD_REQUEST)


def register(request):
    """
    - When POST is received, it performs user data check & registration
    """

    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        password_hash = core.make_hash(password)  # make password hash

        user_db = UserData.objects(username=email)

        if not user_db.count():
            token = core.generate({'type': 'USER', 'email': email})

            tk_ref = Token.objects.with_id(token)
            tk_ref.save()

            user_db = UserData()
            user_db._id = uuid.uuid4().__str__()
            user_db.username = email
            user_db.password = password_hash
            user_db.token = tk_ref.to_dbref()
            user_db.save()
            data = {'id': user_db._id, 'token': tk_ref.token, 'email': user_db.username}
            return http.JsonResponse(data=data, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'User aleready registered.'}, status=HTTPStatus.NOT_MODIFIED)
