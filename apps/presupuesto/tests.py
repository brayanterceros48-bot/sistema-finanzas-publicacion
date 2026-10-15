from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.finanzas.models import Categoria
from .models import Presupuesto


class PresupuestoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='presupuesto@prueba.com',
            email='presupuesto@prueba.com',
            password='Prueba2026!'
        )
        self.categoria = Categoria.objects.create(nombre='Compras')
        self.client.force_login(self.usuario)

    def test_registrar_presupuesto(self):
        respuesta = self.client.post(reverse('registrar_presupuesto'), {
            'categoria': self.categoria.id,
            'monto': '250',
            'mes': '9',
            'anio': '2026',
        })
        self.assertRedirects(respuesta, reverse('lista_presupuestos'))
        presupuesto = Presupuesto.objects.get(usuario=self.usuario)
        self.assertEqual(presupuesto.monto, Decimal('250.00'))
