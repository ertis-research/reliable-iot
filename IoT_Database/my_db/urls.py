from my_db.restful_API.modular_views import web_login_register_view
from my_db.restful_API.modular_views import docker_commands_view
from my_db.restful_API.modular_views import app_resource_usage
from my_db.restful_API.modular_views import application_view
from my_db.restful_API.modular_views import register_view
from my_db.restful_API.modular_views import endpoint_view
from my_db.restful_API.modular_views import resource_view
from my_db.restful_API.modular_views import token_view
from my_db.restful_API.modular_views import shadow_view
from my_db.restful_API.modular_views import user_view
from django.urls import path

urlpatterns = [
    # THESE ROUTES ARE FOR REAL DEVICES
    path('register/', register_view.register_device),
    path('getPhysicalDevice/<str:dev_id>/', register_view.get_physical_device),
    path('deletePhysicalDevice/<str:dev_id>/', register_view.delete_device),
    path('updatePhysicalDevice/<str:dev_id>/', register_view.update_device),
    path('getDeviceStatus/<str:dev_id>/', register_view.device_status),

    # THESE ROUTES ARE FOR ENDPOINTS
    path('storeEndpoint/', endpoint_view.store_endpoint),
    path('getEndpointById/<str:ep_id>/', endpoint_view.get_endpoint_by_id),
    path('getEndpointByLeshanId/<str:leshan_id>/', endpoint_view.get_endpoint_by_leshanid),
    path('updateEndpoint/<str:ep_id>/', endpoint_view.update_endpoint),

    # THESE ROUTES ARE FOR RESOURCES
    path('storeResource/', resource_view.store_resource),
    path('getResource/<str:res_id>/', resource_view.get_resource),
    path('deleteResource/<str:res_id>/', resource_view.delete_resource),
    path('updateResource/<str:endpoint_id>/', resource_view.update_resource),
    path('getShadowResources/<str:shdw_id>/', resource_view.get_shadow_resources),
    path('getDeviceResources/<str:dev_id>/', resource_view.get_device_resources),
    path('getResourceStatus/<str:res_id>/', resource_view.resource_status),
    path('getSimilarResource/', resource_view.get_similar_resource),

    # THESE ROUTES ARE FOR DOCKER COMMANDS
    path('storeType/', docker_commands_view.store_type),
    path('getTypeCommand/<str:d_type>/', docker_commands_view.get_connector_by_type),
    path('getAllConnectors/', docker_commands_view.get_all),

    # THESE ROUTES ARE FOR TOKEN CRUD
    path('getTokenById/<str:token_id>/', token_view.get_token_by_id),
    path('getTokenByUser/<str:user_id>/', token_view.get_tokens_by_user_id),
    path('getTokenByShadow/<str:shadow_id>/', token_view.get_tokens_by_shadow),
    path('generateToken/', token_view.generate_token),

    # THESE ROUTES ARE FOR TOKEN AUTH
    path('validateToken/', token_view.validate_token),
    path('revokeToken/', token_view.revoke_token),

    # THESE ROUTES ARE FOR SHADOW CRUD
    path('createShadow/', shadow_view.create_shadow),
    path('updateShadow/<str:shdw_id>/', shadow_view.update_shadow),
    path('deleteShadow/<str:shdw_id>/', shadow_view.delete_shadow),
    path('getShadowsByUser/<str:user_id>/', shadow_view.get_shadows_by_user_id),
    path('getShadowById/<str:shdw_id>/', shadow_view.get_shadow_by_id),
    path('getShadowTokens/<str:shdw_id>/', shadow_view.get_shadow_tokens),
    path('getShadowDevices/<str:shdw_id>/', shadow_view.get_shadow_devices),

    # THESE ROUTES ARE FOR APPS
    path('getAllApps/', application_view.get_all),
    path('storeOrUpdateApp/<str:name>/', application_view.store_or_update_app),
    path('deleteApp/<str:name>/', application_view.delete_app),

    # THESE ROUTES ARE FOR RESOURCE USAGE
    path('getUsageByEpShadow/<str:ep_id>/<str:shdw_id>/', app_resource_usage.get_resource_use_by_epid_shdwid),

    # THESE ROUTES ARE FOR USER CRUD
    path('updateUser/<str:usr_id>/', user_view.update_user),

    # THESE ROUTES ARE FOR LOGIN / LOG OUT AND REGISTER
    path('login/', web_login_register_view.login),
    path('registerUser/', web_login_register_view.register),
]

