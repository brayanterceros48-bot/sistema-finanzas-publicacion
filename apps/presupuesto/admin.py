from django.contrib import admin

from .models import Presupuesto


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'categoria', 'monto', 'mes', 'anio', 'fecha_creacion')
    search_fields = ('usuario__username', 'usuario__email', 'categoria__nombre')
    list_filter = ('anio', 'mes', 'categoria')
