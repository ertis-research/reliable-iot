from .views import authentication_view
from .views import connector_view
from .views import resources_view
from .views import devices_view
from .views import shaodw_view
from .views import token_view

from django.urls import path


urlpatterns = [
    path('', authentication_view.login_or_register),
    path('login/', authentication_view.login),
    path('logout/', authentication_view.logout),
    path('register/', authentication_view.register),
    path('profile/', authentication_view.profile),


    path('newShadow/', shaodw_view.new_shadow),
    path('deleteShadow/<str:shdw_id>/', shaodw_view.delete_shadow),
    path('editShadow/<str:shdw_id>/', shaodw_view.edit_shadow),
    path('viewShadowResources/<str:shdw_id>/', resources_view.shadow_resources),


    path('connectors/', connector_view.connectors),
    path('newConnector/', connector_view.new_connector),


    path('viewDevices/<str:shdw_id>/', devices_view.devices),
    path('viewDeviceResources/<str:dev_id>/', resources_view.dev_resources),


    path('viewTokens/<str:shdw_id>/', token_view.tokens),
    path('newToken/<str:shdw_id>/', token_view.new_token),

    path('applications/', shaodw_view.view_applications),
]
