import leshan_monitor
import aux_functions
import os


# we get tha environment vars(Device Token and Device ID)
token = os.environ.get('IOT_DEVICE_TOKEN')
real_device_id = os.environ.get('IOT_CONNECTOR_ID')
shadow_device_id = os.environ.get('SHADOW_ID')
device_data = aux_functions.get_real_device(real_device_id, token)

if device_data:
    NEST_API_URL = 'http://{}:{}/event'.format(device_data['ip'], device_data['port'])
    leshan_monitor.get_data_stream(token, NEST_API_URL, device_data, shadow_device_id)
