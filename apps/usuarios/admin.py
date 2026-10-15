from django.contrib import admin

from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre_completo',
        'correo_usuario',
        'fecha_registro',
    )

    search_fields = (
        'nombre_completo',
        'usuario__username',
        'usuario__email',
    )

    list_filter = (
        'fecha_registro',
    )

    @admin.display(description='Correo electrónico')
    def correo_usuario(self, obj):
        return obj.usuario.email