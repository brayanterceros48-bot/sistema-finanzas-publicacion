from django.contrib import admin

from .models import Categoria, Gasto, GastoPendiente, Ingreso, MetaAhorro


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'usuario')
    search_fields = ('nombre', 'usuario__username', 'usuario__email')
    list_filter = ('usuario',)


@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'descripcion', 'monto', 'fecha', 'tipo')
    search_fields = ('descripcion', 'usuario__username', 'usuario__email')
    list_filter = ('tipo', 'fecha')


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'descripcion', 'categoria', 'monto', 'fecha', 'tipo')
    search_fields = ('descripcion', 'usuario__username', 'usuario__email', 'categoria__nombre')
    list_filter = ('tipo', 'categoria', 'fecha')


@admin.register(GastoPendiente)
class GastoPendienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'descripcion', 'categoria', 'monto', 'fecha_limite', 'estado')
    search_fields = ('descripcion', 'usuario__username', 'usuario__email', 'categoria__nombre')
    list_filter = ('estado', 'fecha_limite', 'categoria')


@admin.register(MetaAhorro)
class MetaAhorroAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'nombre', 'monto_objetivo', 'monto_actual', 'fecha_objetivo', 'estado')
    search_fields = ('nombre', 'usuario__username', 'usuario__email')
    list_filter = ('estado', 'fecha_objetivo')
