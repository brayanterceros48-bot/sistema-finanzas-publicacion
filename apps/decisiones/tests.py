from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.finanzas.models import Categoria, Gasto, Ingreso


class DecisionesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='decision@prueba.com',
            email='decision@prueba.com',
            password='Prueba2026!'
        )
        self.categoria = Categoria.objects.create(nombre='Alimentación')
        Ingreso.objects.create(
            usuario=self.usuario,
            descripcion='Ingreso de prueba',
            monto=Decimal('1500.00'),
            fecha='2026-09-29',
            tipo='fijo',
        )
        Gasto.objects.create(
            usuario=self.usuario,
            categoria=self.categoria,
            descripcion='Alimentación',
            monto=Decimal('200.00'),
            fecha='2026-09-29',
            tipo='variable',
        )
        self.client.force_login(self.usuario)

    def test_consulta_decision_responde(self):
        respuesta = self.client.post(
            reverse('consultar_decision'),
            {'pregunta': '¿Cuánto dinero tengo disponible?'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'disponible')
