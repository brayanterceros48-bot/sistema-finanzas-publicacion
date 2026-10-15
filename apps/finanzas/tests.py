from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Gasto, GastoPendiente, Ingreso, MetaAhorro


class FinanzasTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario@prueba.com',
            email='usuario@prueba.com',
            password='Prueba2026!'
        )
        self.otro_usuario = User.objects.create_user(
            username='otro@prueba.com',
            email='otro@prueba.com',
            password='Prueba2026!'
        )
        self.categoria = Categoria.objects.create(nombre='Alimentación')
        self.client.force_login(self.usuario)

    def test_registrar_ingreso(self):
        respuesta = self.client.post(reverse('registrar_ingreso'), {
            'descripcion': 'Apoyo mensual',
            'monto': '1500',
            'fecha': '2026-09-29',
            'tipo': 'fijo',
        })
        self.assertRedirects(respuesta, reverse('lista_ingresos'))
        ingreso = Ingreso.objects.get(usuario=self.usuario)
        self.assertEqual(ingreso.monto, Decimal('1500.00'))

    def test_registrar_gasto_aisla_al_usuario(self):
        gasto = Gasto.objects.create(
            usuario=self.otro_usuario,
            categoria=self.categoria,
            descripcion='Gasto privado',
            monto=Decimal('100.00'),
            fecha=date(2026, 9, 29),
            tipo='variable',
        )
        respuesta = self.client.get(reverse('editar_gasto', args=[gasto.id]))
        self.assertEqual(respuesta.status_code, 404)

    def test_completar_pendiente_sin_categoria_permite_elegirla(self):
        pendiente = GastoPendiente.objects.create(
            usuario=self.usuario,
            descripcion='Material universitario',
            monto=Decimal('100.00'),
            fecha_limite=date(2026, 10, 2),
        )
        respuesta = self.client.post(
            reverse('completar_gasto_pendiente', args=[pendiente.id]),
            {'categoria': self.categoria.id},
        )
        self.assertRedirects(respuesta, reverse('lista_gastos_pendientes'))
        pendiente.refresh_from_db()
        self.assertEqual(pendiente.estado, 'completado')
        self.assertEqual(pendiente.categoria_id, self.categoria.id)
        gasto = Gasto.objects.get(descripcion='Material universitario')
        self.assertEqual(gasto.monto, Decimal('100.00'))
        self.assertEqual(gasto.categoria_id, self.categoria.id)

    def test_meta_ahorro_calcula_progreso(self):
        meta = MetaAhorro.objects.create(
            usuario=self.usuario,
            nombre='Computadora',
            monto_objetivo=Decimal('5000.00'),
            monto_actual=Decimal('1000.00'),
        )
        self.assertEqual(meta.monto_actual / meta.monto_objetivo * 100, Decimal('20.00'))
