from django.conf import settings
from django.db import models

from apps.finanzas.models import Categoria


class Presupuesto(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presupuestos'
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='presupuestos'
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    mes = models.PositiveSmallIntegerField()

    anio = models.PositiveIntegerField()

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        ordering = [
            '-anio',
            '-mes',
            'categoria__nombre'
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    'usuario',
                    'categoria',
                    'mes',
                    'anio'
                ],
                name='presupuesto_unico_por_categoria_periodo'
            )

        ]


    def __str__(self):

        return (
            f'{self.categoria.nombre} - '
            f'Bs {self.monto} - '
            f'{self.mes}/{self.anio}'
        )