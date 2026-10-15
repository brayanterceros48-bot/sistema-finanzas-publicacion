from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario


class UsuariosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario@prueba.com',
            email='usuario@prueba.com',
            password='Prueba2026!'
        )
        PerfilUsuario.objects.create(
            usuario=self.usuario,
            nombre_completo='Usuario de Prueba'
        )

    def test_pagina_principal_envia_al_login_si_no_hay_sesion(self):
        respuesta = self.client.get(reverse('pagina_principal'))
        self.assertRedirects(respuesta, reverse('login'))

    def test_login_funciona(self):
        respuesta = self.client.post(
            reverse('login'),
            {'correo': 'usuario@prueba.com', 'password': 'Prueba2026!'},
        )
        self.assertRedirects(respuesta, reverse('inicio'))

    def test_inicio_requiere_autenticacion(self):
        respuesta = self.client.get(reverse('inicio'))
        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={reverse('inicio')}",
        )
