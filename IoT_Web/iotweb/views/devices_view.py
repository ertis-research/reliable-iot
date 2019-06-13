from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def devices(request, shdw_id):
    """
    GET request: renders the physical devices page
    POST request: It's a request to delete one physical device
    """

    user = User.get_instance()

    if request.POST:  # REQUEST TO DELETE DEVICE
        url = UM.DB_URL + 'deletePhysicalDevice/{}/'.format(request.POST['device_id'])
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            return redirect('/viewDevices/{}/'.format(shdw_id))
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/viewDevices/{}/'.format(shdw_id)
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))

    else:  # GET - RENDER THE TEMPLATE WITH PHYSICAL DEVICES

        template = loader.get_template('../templates/physical_devices.html')

        url = UM.DB_URL + 'getShadowDevices/{}/'.format(shdw_id)
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            devices_list = json.loads(req.text)['devices']
            context = {'devices': [], 'shadow_id': shdw_id, 'email': user.user_email}
            if devices_list:
                for device in devices_list:
                    json_object = json.loads(device)

                    # CHECK THIS AGAIN
                    url_token = UM.DB_URL + 'getTokenById/{}/'.format(json_object['token'])
                    res_tok = requests.get(url=url_token, headers=headers)
                    token = json.loads(res_tok.text)['token']
                    json_object['token'] = token  # we replace token id with token value

                    json_object['id'] = json_object['_id']

                    url_status = UM.DB_URL + 'getDeviceStatus/{}/'.format(json_object['_id'])
                    req_status = requests.get(url=url_status, headers=headers)
                    json_object['STATUS'] = json.loads(req_status.text)['status']

                    context['devices'].append(json_object)

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



