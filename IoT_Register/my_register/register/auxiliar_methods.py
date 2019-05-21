import requests
import json

DB_HOSTNAME = 'mongoapi'
DB_PORT = '80'


def extract_request_data(request):
    '''
    When a register request comes, this method will get all needed data and returns it as a dict
    :param request:HTTP Request
    :return: data:dict
    '''
    data = {
        'Type': request.POST['type'],
        'Ip': request.POST['ip'],
        'Port': request.POST['port'],
        'Token': request.POST['token'],
        'Mac': request.POST['MAC'],
        'Shadow_id': request.POST['shadow_id']
    }

    return data


def register_store_request(device_data_to_store, token):
    '''
    Given a non empty dict of values to store, this method requests de DB in order to store the data that has been
    passed as parameter.

    :param device_data_to_store:dict
    :param token:String
    :return: response:dict
    '''
    url = 'http://{}:{}/register/'.format(DB_HOSTNAME, DB_PORT)
    headers = {'Authorization': 'Token {}'.format(token)}
    req = requests.post(url=url, data=device_data_to_store, headers=headers)

    if req.status_code == 200:
        response = {'status_code': 200}
        response.update(json.loads(req.text))
    else:
        response = {'status_code': req.status_code, 'message': req.text}

    return response


def get_docker_image(token, device_type=None):
    '''
    Given a type, this method requests the DB for the command of that type
    :param device_type:String
    :param token:String
    :return: image:String, status_code:Integer, message:String
    '''

    if device_type:
        url = 'http://{}:{}/getTypeCommand/{}/'.format(DB_HOSTNAME, DB_PORT, device_type)
        headers = {'Authorization': 'Token {}'.format(token)}

        req = requests.get(url=url, headers=headers)

        if req.status_code == 200:
            image = json.loads(req.text)['image']
        else:
            image = 'x'

        status_code = req.status_code
        message = req.text

    else:
        image = 'x'
        status_code = 404
        message = 'Not found'

    return image, status_code, message


def delete_real_device(device_id, token):
    url = 'http://{}:{}/deletePhysicalDevice/{}/'.format(DB_HOSTNAME, DB_PORT, device_id)
    headers = {'Authorization': 'Token {}'.format(token)}
    requests.delete(url=url, headers=headers)


def check_token_validation(token):
    '''
    Given a string token this method checks the validity of the token

    :param token:String ('Token mytoken')
    :return: Bool
    '''
    url = 'http://{}:{}/validateToken/'.format(DB_HOSTNAME, DB_PORT)
    headers = {'Authorization': 'Token {}'.format(token)}
    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        return 1
    else:
        return 0


