from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.consultar_decision,
        name='consultar_decision'
    ),

]