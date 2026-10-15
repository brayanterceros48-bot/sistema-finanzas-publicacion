from django.urls import path

from . import views

urlpatterns = [
    path('ingresos/', views.lista_ingresos, name='lista_ingresos'),
    path('ingresos/registrar/', views.registrar_ingreso, name='registrar_ingreso'),
    path('ingresos/editar/<int:ingreso_id>/', views.editar_ingreso, name='editar_ingreso'),
    path('ingresos/eliminar/<int:ingreso_id>/', views.eliminar_ingreso, name='eliminar_ingreso'),

    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/registrar/', views.registrar_gasto, name='registrar_gasto'),
    path('gastos/editar/<int:gasto_id>/', views.editar_gasto, name='editar_gasto'),
    path('gastos/eliminar/<int:gasto_id>/', views.eliminar_gasto, name='eliminar_gasto'),

    path('gastos-pendientes/', views.lista_gastos_pendientes, name='lista_gastos_pendientes'),
    path('gastos-pendientes/registrar/', views.registrar_gasto_pendiente, name='registrar_gasto_pendiente'),
    path('gastos-pendientes/completar/<int:gasto_pendiente_id>/', views.completar_gasto_pendiente, name='completar_gasto_pendiente'),
    path('gastos-pendientes/eliminar/<int:gasto_pendiente_id>/', views.eliminar_gasto_pendiente, name='eliminar_gasto_pendiente'),

    path('metas-ahorro/', views.lista_metas_ahorro, name='lista_metas_ahorro'),
    path('metas-ahorro/registrar/', views.registrar_meta_ahorro, name='registrar_meta_ahorro'),
    path('metas-ahorro/agregar/<int:meta_id>/', views.agregar_ahorro_meta, name='agregar_ahorro_meta'),
    path('metas-ahorro/completar/<int:meta_id>/', views.completar_meta_ahorro, name='completar_meta_ahorro'),
    path('metas-ahorro/eliminar/<int:meta_id>/', views.eliminar_meta_ahorro, name='eliminar_meta_ahorro'),

    path('historial/', views.historial, name='historial'),
]
