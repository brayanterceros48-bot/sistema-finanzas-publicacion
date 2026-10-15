from django.contrib.auth.models import User
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categorias_financieras'
    )

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ingreso(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ingresos'
    )
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    fecha = models.DateField()
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('fijo', 'Fijo'),
            ('variable', 'Variable'),
        ],
        default='variable'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ingreso'
        verbose_name_plural = 'Ingresos'
        ordering = ['-fecha', '-fecha_registro']

    def __str__(self):
        return f'{self.descripcion} - Bs {self.monto}'


class Gasto(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gastos'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='gastos'
    )
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    fecha = models.DateField()
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('fijo', 'Fijo'),
            ('variable', 'Variable'),
        ],
        default='variable'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha', '-fecha_registro']

    def __str__(self):
        return f'{self.descripcion} - Bs {self.monto}'


class GastoPendiente(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gastos_pendientes'
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos_pendientes'
    )

    descripcion = models.CharField(
        max_length=200
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha_limite = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
        ],
        default='pendiente'
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Gasto pendiente'
        verbose_name_plural = 'Gastos pendientes'
        ordering = [
            'estado',
            'fecha_limite',
            '-fecha_registro'
        ]

    def __str__(self):
        return (
            f'{self.descripcion} - '
            f'Bs {self.monto} - '
            f'{self.fecha_limite}'
        )

class MetaAhorro(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='metas_ahorro'
    )

    nombre = models.CharField(
        max_length=200
    )

    monto_objetivo = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    monto_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    fecha_objetivo = models.DateField(
        null=True,
        blank=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=20,
        choices=[
            ('activa', 'Activa'),
            ('completada', 'Completada'),
        ],
        default='activa'
    )

    class Meta:
        verbose_name = 'Meta de ahorro'
        verbose_name_plural = 'Metas de ahorro'
        ordering = ['estado', 'fecha_objetivo', '-fecha_registro']

    def __str__(self):
        return (
            f'{self.nombre} - '
            f'Bs {self.monto_actual} / '
            f'Bs {self.monto_objetivo}'
        )