from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import loader
from http.server import HTTPStatus
from .User import User

import iotweb.views.urls_and_messages as UM
import requests
import json


def login_or_register(request):
    """This endpoint renders the root page"""
    template = loader.get_template('../templates/login_or_register.html')
    return HttpResponse(template.render({}, request))


def login(request):
    """
    GET request: renders the login page
    POST request: authenticates the user and redirects to user homepage
    """
    if request.POST:
        url = UM.DB_URL + 'login/'
        data = request.POST
        req = requests.post(url=url, data=data)

        if req.status_code == 200:
            user_data = json.loads(req.text)

            try:
                # if an instance aleready exists it throws exception
                User(user_data['id'], user_data['token'], user_data['email'])
            except:
                user = User.get_instance()
                user.user_id = user_data['id']
                user.user_token = user_data['token']
                user.user_email = user_data['email']

            return redirect('/profile/')
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': HTTPStatus.EXPECTATION_FAILED,
                       'message': req.text,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/login/'
                       }
            return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/login.html')
        return HttpResponse(template.render({}, request))


def logout(request):
    """
    Logs the user out revoking his session token and redirecting to login page
    """
    user = User.get_instance()
    user.user_id = None
    user.user_email = None

    url = UM.DB_URL + 'revokeToken/'
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    requests.get(url=url, headers=headers)

    user.user_token = None

    template = loader.get_template('../templates/login.html')
    return HttpResponse(template.render({}, request))


def register(request):
    """
    GET request: renders the register page
    POST request: registers the user and redirects him to user homepage
    """
    if request.POST:
        url = UM.DB_URL + 'registerUser/'
        data = request.POST
        req = requests.post(url=url, data=data)

        if req.status_code == 200:
            user_data = json.loads(req.text)

            try:
                # if an instance aleready exists it throws exception
                User(user_data['id'], user_data['token'], user_data['email'])
            except:
                user = User.get_instance()
                user.user_id = user_data['id']
                user.user_token = user_data['token']
                user.user_email = user_data['email']

            return redirect('/profile/')
        else:
            template = loader.get_template('../templates/error_page.html')
            context = {'code_error': HTTPStatus.EXPECTATION_FAILED,
                       'message': UM.ALREADY_REGISTERED,
                       'error_name': HTTPStatus(req.status_code).phrase,
                       'back': '/login/'
                       }
            return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('../templates/register.html')
        return HttpResponse(template.render({}, request))


def profile(request):
    """Renders user's main page"""
    template = loader.get_template('../templates/shadows.html')
    user = User.get_instance()

    url = UM.DB_URL+'getShadowsByUser/{}/'.format(user.user_id)
    headers = {'Authorization': 'Token {}'.format(user.user_token)}
    req = requests.get(url=url, headers=headers)

    if req.status_code == 200:
        shdw_list = json.loads(req.text)['shadows']
        context = {'shadows': [], 'email': user.user_email}
        if shdw_list:
            for shadow in shdw_list:
                json_object = json.loads(shadow)
                json_object['id'] = json_object['_id']  # because error occurrs in html if i try to do {{shadow._id}}
                context['shadows'].append(json_object)

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