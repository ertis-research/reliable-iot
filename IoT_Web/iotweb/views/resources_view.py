from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def shadow_resources(request, shdw_id):
    user = User.get_instance()

    template = loader.get_template('../templates/resources.html')

    url = UM.DB_URL + 'getShadowResources/{}/'.format(shdw_id)
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    req = requests.get(url=url, headers=headers)

    if req.status_code == 200:
        resources_list = json.loads(req.text)['resources']
        context = {'resources': {}, 'email': user.user_email, 'shadow_id': shdw_id}

        if resources_list:
            json_object_list = [json.loads(x) for x in resources_list]
            frequency = {}

            for resource in json_object_list:
                if resource['type'] in frequency:
                    frequency[resource['type']] += 1
                else:
                    frequency[resource['type']] = 1

            context['resources'] = frequency

        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/error_page.html')
        context = {'code_error': req.status_code,
                   'message': req.text,
                   'error_name': HTTPStatus(req.status_code).phrase,
                   'back': '/profile/'
                   }
        if req.status_code == 401:
            context['message'] = context['message'] + UM.REFRESH_TOKEN
            context['back'] = '/login/'

        return HttpResponse(template.render(context, request))


def dev_resources(request, dev_id):
    user = User.get_instance()

    if request.POST:  # REQUEST TO DELETE A RESOURCE
        url = UM.DB_URL + 'deleteResource/{}/'.format(request.POST['resource_id'])  # must be done in database
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            return redirect('/viewDeviceResources/{}/'.format(dev_id))
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/viewDeviceResources/{}/'.format(dev_id)
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))
    else:  # GET - RENDER THE TEMPLATE WITH DEVICE RESOURCES

        template = loader.get_template('../templates/resources.html')

        url = UM.DB_URL + 'getDeviceResources/{}/'.format(dev_id)
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            resources = json.loads(req.text)
            context = {'resources': {}, 'email': user.user_email, 'device_id': dev_id}
            if resources:
                for ep, resources_list in resources.items():
                    for res in resources_list:
                        json_object = json.loads(res)
                        json_object['id'] = json_object['_id']

                        url_status = UM.DB_URL + 'getResourceStatus/{}/'.format(json_object['_id'])
                        req_status = requests.get(url=url_status, headers=headers)
                        json_object['STATUS'] = json.loads(req_status.text)['status']

                        if ep in context['resources']:
                            context["resources"][ep].append(json_object)
                        else:
                            context["resources"][ep] = [json_object]

            return HttpResponse(template.render(context, request))
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/profile/'
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))

