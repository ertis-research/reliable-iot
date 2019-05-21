from my_db.db_mongo.model import DeviceTypeDockerCommand
from my_db.restful_API.auth import core
from my_db.db_mongo import mongo_setup
from http import HTTPStatus
from django import http
import uuid

mongo_setup.global_init()  # makes connection with db


def get_connector_by_type(request, d_type=None):
    """
    Given a connector Type, this method searches it in the DB and returns it if found.
    """
    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'
        # CHECK THE TOKEN
        if core.validate(token):
            docker_images = DeviceTypeDockerCommand.objects(type=d_type)
            if docker_images.count():
                d_image = docker_images.first()
                return http.JsonResponse(status=HTTPStatus.OK, data={'image': d_image.image})
            else:
                return http.JsonResponse(data={'message': 'This type of device is not supported.'}, status=HTTPStatus.NOT_IMPLEMENTED)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def get_all(request):
    """This method returns all the IoT Connector Types from the database"""

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):
            docker_images = DeviceTypeDockerCommand.objects()
            images_list = []

            for img in docker_images:
                images_list.append(img.to_json())

            return http.JsonResponse(data={'images': images_list}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def store_type(request):
    '''
    This method expects a dict passed in the body with the following fields:
    {
    type : text:String,
    image: text:String
    }

    With this information it store in the database a new IoT Connector Type.

    WARNING: THIS METHOD DOESN'T CHECK WHETHER THE SYSTHEM SUPPORTS OR NOT THE NEW REGISTERED TYPE.
    IT DOESN'T EITHER CHECKS IF THE DOCKER IMAGE EXISTS.

    '''

    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        # CHECK THE TOKEN
        if core.validate(token):
            new_connector = DeviceTypeDockerCommand()

            if 'type' in request.POST:
                new_connector.type = request.POST['type']

                # If It's aleready in the database, we don't add it again
                if DeviceTypeDockerCommand.objects(type=request.POST['type']).count():
                    return http.JsonResponse(data={'message': "Type aleready registered"}, status=HTTPStatus.NOT_MODIFIED)

            else:
                return http.JsonResponse(data={'message': "Type was not passed"}, status=HTTPStatus.BAD_REQUEST)

            if 'image' in request.POST:
                new_connector.image = request.POST['image']
            else:
                return http.JsonResponse(data={'message': "Image name was not passed"}, status=HTTPStatus.BAD_REQUEST)
            new_connector._id = uuid.uuid4().__str__()
            new_connector.save()
            return http.JsonResponse(data={'message': 'IoT Connector stored successfully'}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"}, status=HTTPStatus.BAD_REQUEST)
