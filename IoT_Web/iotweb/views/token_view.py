from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def tokens(request, shdw_id):
    """
    GET request: renders the token page
    POST request: revokes a specific token
    """
    user = User.get_instance()

    if not request.POST:
        template = loader.get_template('../templates/shadow_tokens.html')

        url = UM.DB_URL+'getShadowTokens/{}/'.format(shdw_id)
        headers = {'Authorization': 'Token {}'.format(user.user_token)}
        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            tkn_list = json.loads(req.text)['tokens']
            context = {'tokens': [], 'email': user.user_email}

            if tkn_list:
                for tkn in tkn_list:
                    json_object = json.loads(tkn)
                    if json_object["revoked"]:
                        json_object['status'] = "REVOKED"
                    else:
                        json_object['status'] = "VALID"

                    context['tokens'].append(json_object)

            context['shadow'] = shdw_id
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

    else:  # it's a post (to revoke a token)
        url = UM.DB_URL + 'revokeToken/'
        token = request.POST['token']
        headers = {'Authorization': 'Token {}'.format(token)}
        req = requests.get(url=url, headers=headers)  # HERE THE TOKEN IS REVOKED
        if req.status_code == 200:
            return redirect('/viewDevices/{}/'.format(shdw_id))
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req.status_code,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/login/'
                       }
            if req.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))


def new_token(request, shdw_id):
    '''generates a new token and refresh the page'''
    user = User.get_instance()

    url = UM.DB_URL+'generateToken/'
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    data = {'shadow_id': shdw_id, 'type': 'DEVICE'}
    req = requests.post(url=url, data=data, headers=headers)  # HERE THE TOKEN IS CREATED

    if req.status_code == 200:
        tkn_id = json.loads(req.text)['token']

        url_update_shadow = UM.DB_URL+'updateShadow/{}/'.format(shdw_id)
        data_update = {'token': tkn_id}

        req_update = requests.post(url=url_update_shadow, data=data_update, headers=headers)  # HERE WE UPDATE THE SHADOW

        if req_update.status_code == 200:
            return redirect('/viewTokens/{}/'.format(shdw_id))
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': req_update.status_code,
                       'message': req_update.text,
                       'error_name': HTTPStatus(req_update.status_code).phrase,
                       'back': '/viewTokens/{}/'.format(shdw_id)
                       }
            if req_update.status_code == 401:
                context['message'] = context['message'] + UM.REFRESH_TOKEN
                context['back'] = '/login/'

            return HttpResponse(template.render(context, request))
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
