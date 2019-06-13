from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def connectors(request):
    """Renders the page of the Iot Connectors"""
    user = User.get_instance()

    template = loader.get_template('../templates/iot_connectors.html')
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    url_connectors = UM.DB_URL + 'getAllConnectors/'
    req = requests.get(url=url_connectors, headers=headers)

    if req.status_code == 200:
        connector_list = json.loads(req.text)['images']
        context = {'connectors': [], 'email': user.user_email}

        if connector_list:
            for conn in connector_list:
                conn_json_object = json.loads(conn)
                context['connectors'].append(conn_json_object)

        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/error_page.html')
        context = {'code_error': req.status_code,
                   'message': req.text,
                   'error_name': HTTPStatus(req.status_code).phrase,
                   'back': '/login/'
                   }
        if req.status_code == 401:
            context['message'] = context['message'] + UM.REFRESH_TOKEN

        return HttpResponse(template.render(context, request))


def new_connector(request):
    """
    GET request: renders the page for a new connector
    POST request: Stores the connector and redirects to the connectors view
    """
    user = User.get_instance()

    if request.POST:
        url = UM.DB_URL+'storeType/'
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        data = {}

        data['image'] = request.POST['inputImage']
        data['type'] = request.POST['inputType']

        req = requests.post(url=url, data=data, headers=headers)

        if req.status_code == HTTPStatus.OK or req.status_code == HTTPStatus.NOT_MODIFIED:
            return redirect('/connectors/')
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/newConnector/'
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/new_connector.html')
        return HttpResponse(template.render({'email': user.user_email}, request))
