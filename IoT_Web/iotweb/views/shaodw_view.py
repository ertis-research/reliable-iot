from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def new_shadow(request):
    user = User.get_instance()

    if request.POST:
        url = UM.DB_URL+'createShadow/'
        data = request.POST
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.post(url=url, data=data, headers=headers)

        if req.status_code == 200:
            shadow = json.loads(req.text)['shadow']
            shadow_id = json.loads(shadow)['_id']  # this will go to the user
            url2 = UM.DB_URL+'updateUser/{}/'.format(user.user_id)
            data2 = {'shadow': shadow_id}
            requests.post(url=url2, data=data2, headers=headers)  # WE UPDATE HERE THE USER

            return redirect('/profile/')
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/newShadow/'
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/new_shadow.html')
        return HttpResponse(template.render({'email': user.user_email}, request))


def delete_shadow(request, shdw_id):
    user = User.get_instance()

    # first we delete it's associated devices
    url_devices = UM.DB_URL + 'getShadowDevices/{}/'.format(shdw_id)
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    req = requests.get(url=url_devices, headers=headers)

    devices_ids = []
    if req.status_code == 200:
        devices_ids = [json.loads(dev)['_id'] for dev in json.loads(req.text)['devices']]

    url_delete_device = UM.DB_URL + 'deletePhysicalDevice/{}/'

    for dev_id in devices_ids:
        url_delete_device.format(dev_id)
        requests.get(url=url_delete_device, headers=headers)

    url = UM.DB_URL + 'deleteShadow/{}/'.format(shdw_id)
    req = requests.get(url=url, headers=headers)

    if req.status_code == 200:
        return redirect('/profile/')
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


def edit_shadow(request, shdw_id):
    user = User.get_instance()

    if request.POST:
        url = UM.DB_URL + 'updateShadow/{}/'.format(shdw_id)
        data = request.POST
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.post(url=url, data=data, headers=headers)

        if req.status_code == 200:
            return redirect('/profile/')
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/editShadow/{}/'.format(shdw_id)
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/edit.html')
        url = UM.DB_URL + 'getShadowById/{}/'.format(shdw_id)
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            data = json.loads(req.text)['shadow']
            context = {'data': json.loads(data), 'email': user.user_email}
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


def view_applications(request):
    user = User.get_instance()

    template = loader.get_template('../templates/applications.html')
    headers = {'Authorization': 'Token {}'.format(user.user_token)}

    url_connectors = UM.DB_URL + 'getAllApps/'
    req = requests.get(url=url_connectors, headers=headers)
    context = {'apps': [], 'email': user.user_email}

    if req.status_code == 200:
        apps_list = json.loads(req.text)['apps']

        if apps_list:
            for app in apps_list:
                conn_json_object = json.loads(app)
                context['apps'].append(conn_json_object)

    return HttpResponse(template.render(context, request))
