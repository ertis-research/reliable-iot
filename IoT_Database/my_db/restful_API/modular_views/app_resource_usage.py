from my_db.db_mongo.model import ResourceUse, Shadow, IotConnector, Endpoint, Resource, Application
from my_db.restful_API.auth import core
from my_db.db_mongo import mongo_setup
from http import HTTPStatus
from django import http
import uuid
import json

mongo_setup.global_init()  # makes connection with db


def get_resource_use_by_epid_shdwid(request, ep_id, shdw_id):
    """
    This method returns the usages of resources that belong to a specific endpoint and to a specific shadow device
    """

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):
            res_usages_fetched = ResourceUse.objects(endpoint=ep_id, shadow=shdw_id)
            res_usages_list = []

            for res_usage in res_usages_fetched:
                jsn = res_usage.to_json()
                jsn = json.loads(jsn)
                jsn['resource_code'] = res_usage.resource.type  # we add the resource code too bc we need it :D

                res_usages_list.append(json.dumps(jsn))

            return http.JsonResponse(data={'usages': res_usages_list}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def get_similar_logic(request, res_code, operation, shdw_id=None):
    """
    Given a Resource code, an Operation and a Shadow Id (optional), this method looks for a similar logic if
    it's already created.
    Note: It only makes sense for operation = OBSERVATION
    """
    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):

            if shdw_id:  # the search could be in one shadow or every shadow
                logic_list = ResourceUse.objects(shadow=shdw_id, operation=operation)
            else:
                logic_list = ResourceUse.objects(operation=operation)

            for logic in logic_list:
                if logic.resource.type == int(res_code):
                    kafka_topic = logic.kafka_topic
                    return http.JsonResponse(data={'kafka_topic': kafka_topic, '_id': logic._id}, status=HTTPStatus.OK)

            # if program reaches this point, no similar logic was found
            return http.JsonResponse(data={'Message': HTTPStatus.NOT_FOUND.name}, status=HTTPStatus.NOT_FOUND)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def create(request):
    """
        This method creates a new usage  entry in the DB.

        data e.g:
        {
            'application': <app_name>,
            'shadow': <shadow_id>,
            'iot_connector': <connector_id>,
            'endpoint': <endpoint_id>,
            'resource': <resource_id>,
            'accessing': <string>,
            'operation': <operation>,
            'kafka_topic': <kafka_topic>
        }

        All fields in the data dict are mandatory.

        """

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):
            data = request.POST

            connector = IotConnector.objects.with_id(data['iot_connector']); connector.save()
            app = Application.objects(name=data['application']).first(); app.save()
            res = Resource.objects.with_id(data['resource']); res.save()
            shdw = Shadow.objects.with_id(data['shadow']); shdw.save()
            ep = Endpoint.objects.with_id(data['endpoint']); ep.save()

            new_usage = ResourceUse()
            new_usage._id = uuid.uuid4().__str__()
            new_usage.applications.append(app.to_dbref())
            new_usage.shadow = shdw.to_dbref()
            new_usage.iot_connector = connector.to_dbref()
            new_usage.endpoint = ep.to_dbref()
            new_usage.resource = res.to_dbref()
            new_usage.accessing = data['accessing']
            new_usage.kafka_topic = data['kafka_topic']
            new_usage.operation = data['operation']
            new_usage.save()

            return http.JsonResponse(data={'usage_id': new_usage._id}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def update(request, usage_id):
    """
    This method updates the usage information in the DB.

    data e.g:
    {
        'shadow': <shadow_id>,
        'iot_connector': <connector_id>,
        'endpoint': <endpoint_id>,
        'resource': <resource_id>,
        'accessing': <string>,
        'kafka_topic': <kafka_topic>,
        'applications': [<app_name>]
    }

    All fields in the data dict are optional.

    """

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):

            data = request.POST
            usage = ResourceUse.objects.with_id(usage_id)  # it could be None (if it's not in the db)

            if usage:
                if 'applications' in data:
                    for app in json.loads(data['applications']):

                        db_app = Application.objects(name=app)
                        if db_app.count():
                            db_app = db_app.first()
                            db_app.save()
                            usage.applications.append(db_app.to_dbref())

                if 'shadow' in data:
                    new_shadow = data['shadow']

                    if new_shadow != usage.shadow:  # we update only if shadows are different
                        shadow = Shadow.objects.with_id(new_shadow)
                        shadow.save()
                        usage.shadow = shadow.to_dbref()

                if 'iot_connector' in data:
                    new_connector = data['iot_connector']

                    if new_connector != usage.iot_connector:  # we update only if connectors are different
                        connector = IotConnector.objects.with_id(new_connector)
                        connector.save()
                        usage.iot_connector = connector.to_dbref()

                if 'endpoint' in data:
                    new_endpoint = data['iot_connector']

                    if new_endpoint != usage.endpoint:  # we update only if endpoints are different
                        endpoint = Endpoint.objects.with_id(new_endpoint)
                        endpoint.save()
                        usage.endpoint = endpoint.to_dbref()

                if 'resource' in data:  # we update always
                    new_resource = Resource.objects.with_id(data['resource'])
                    new_resource.save()
                    usage.resource = new_resource.to_dbref()

                if 'accessing' in data:
                    if usage.accessing != data['accessing']:
                        usage.accessing = data['accessing']

                if 'kafka_topic' in data:  # we update always
                    usage.kafka_topic = data["kafka_topic"]

                usage.save()
                message = "Success!"
            else:
                message = "Fail!"

            return http.JsonResponse(data={'usages': message}, status=HTTPStatus.OK)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)


def delete(request, usage_id):
    """This method removes from de DB an usage"""

    if request.META.get('HTTP_AUTHORIZATION'):  # This checks if token is passed
        token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]  # 'Token adsad' -> ['Token', 'adsad'] -> 'adsad'

        # CHECK THE TOKEN
        if core.validate(token):
            usage = ResourceUse.objects.with_id(usage_id)
            if usage:
                usage.delete()
                message = "Success!"
                status = HTTPStatus.OK
            else:
                message = HTTPStatus.NOT_FOUND.name
                status = HTTPStatus.NOT_FOUND

            return http.JsonResponse(data={'message': message}, status=status)
        else:
            return http.JsonResponse(data={'message': 'Token invalid or expired.'}, status=HTTPStatus.UNAUTHORIZED)
    else:
        return http.JsonResponse(data={'message': "Authentication credentials not provided"},
                                 status=HTTPStatus.BAD_REQUEST)
