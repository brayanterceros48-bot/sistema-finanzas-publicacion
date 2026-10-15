from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

from django.shortcuts import redirect


def pagina_principal(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    return redirect('login')


# ============================================================
# URLS PRINCIPALES
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # ADMINISTRACIÓN
    # --------------------------------------------------------

    path(
        'admin/',
        admin.site.urls
    ),

    # --------------------------------------------------------
    # PÁGINA PRINCIPAL
    # --------------------------------------------------------

    path(
        '',
        pagina_principal,
        name='pagina_principal'
    ),

    # --------------------------------------------------------
    # USUARIOS
    # --------------------------------------------------------

    path(
        '',
        include('apps.usuarios.urls')
    ),

    # --------------------------------------------------------
    # FINANZAS
    # --------------------------------------------------------

    path(
        'finanzas/',
        include('apps.finanzas.urls')
    ),

    # --------------------------------------------------------
    # DECISIONES
    # --------------------------------------------------------

    path(
        'decisiones/',
        include('apps.decisiones.urls')
    ),

    path('presupuesto/', include('apps.presupuesto.urls')),
]