from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

urlpatterns = [

    path('login/', views.iniciar_sesion, name='login'),

    path('registro/', views.registro, name='registro'),

    path('salir/', views.cerrar_sesion, name='logout'),

    path('inicio/', views.inicio, name='inicio'),

    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),

    path(
        'recuperar-password/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='usuarios/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'recuperar-password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path(
        'recuperar-password/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='usuarios/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

]