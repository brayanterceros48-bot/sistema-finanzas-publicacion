from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista_presupuestos, name='lista_presupuestos'),
    path('registrar/', views.registrar_presupuesto, name='registrar_presupuesto'),
    path('editar/<int:presupuesto_id>/', views.editar_presupuesto, name='editar_presupuesto'),
    path('eliminar/<int:presupuesto_id>/', views.eliminar_presupuesto, name='eliminar_presupuesto'),
]
