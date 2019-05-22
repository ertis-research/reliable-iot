from my_db.db_mongo.model import Endpoint, Resource
from my_db.db_mongo import mongo_setup
from my_db.restful_API.auth import core
from django import http
from http import HTTPStatus

import json
import uuid

mongo_setup.global_init()  # makes connection with db


def get_endpoint_by_id(request, ep_id):
    '''
        Given an Endpoint _id, this method fetches the Endpoint from the db and returns it.
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            endpoint = Endpoint.objects.with_id(ep_id)

            if endpoint:
                return http.JsonResponse(data={'message': endpoint.to_json()}, status=HTTPStatus.OK)
            else:
                return http.JsonResponse(data={'message': 'Endpoint does not exist.'}, status=HTTPStatus.NOT_FOUND)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def get_endpoint_by_leshanid(request, leshan_id):
    '''
        Given an Endpoint _id, this method fetches the Endpoint from the db and returns it.
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            endpoint = Endpoint.objects(leshan_id=leshan_id)

            if endpoint.count():
                endpoint = endpoint.first()
                return http.JsonResponse(data={'endpoint_id': endpoint._id}, status=HTTPStatus.OK)
            else:
                return http.JsonResponse(data={'message': 'Endpoint does not exist.'}, status=HTTPStatus.NOT_FOUND)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def store_endpoint(request):
    '''
        This method expects a dict passed in the body with the following fields:
        {
        registrationId : text:String,
        address: text:String
        }

        With this information it store in the database the new Endpoint.
    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            new_endpoint = Endpoint()
            new_endpoint._id = uuid.uuid4().__str__()
            new_endpoint.leshan_id = request.POST['registrationId']
            new_endpoint.address = request.POST['address']
            new_endpoint.name = request.POST['name']

            try:
                new_endpoint.save()
                status_to_return = HTTPStatus.OK
                data = {'endpoint_id': new_endpoint.pk}
            except:  # Data-Wrong or Connection Failed
                return http.JsonResponse({'message': 'Wrong data or database connection failed'}, status=HTTPStatus.BAD_REQUEST)

            return http.JsonResponse(data=data, status=status_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)


def update_endpoint(request, ep_id):
    '''Given an Endpoint leshan_id, this method performs the update of the database object related to the given id.'''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            data = request.POST
            endpoint = Endpoint.objects.with_id(ep_id)  # it gives back a QuerySet

            if endpoint:  # if any endpoint fetched
                if 'event' in data:
                    endpoint.events.append(data['event'])

                if 'status' in data:
                    endpoint.available = bool(int(data['status']))

                    for res in endpoint.resources:
                        res.status = bool(int(data['status']))
                        res.save()

                if 'resources' in data:
                    for res in json.loads(data['resources']):  # data['resources'] = [resID, ...]
                        associated_res = Resource.objects.with_id(res)
                        associated_res.save()
                        endpoint.resources.append(associated_res.to_dbref())  # append endpoint ref

                endpoint.save()
                data_to_return = {'message': 'Success!'}
                code_to_return = HTTPStatus.OK

            else:  # if no endpoint fetched
                data_to_return = {'message': 'NOT MODIFIED'}
                code_to_return = HTTPStatus.NOT_MODIFIED

            return http.JsonResponse(data=data_to_return, status=code_to_return)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)
