from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.utils import timezone

from apps.finanzas.models import Gasto, GastoPendiente, Ingreso, MetaAhorro
from apps.presupuesto.models import Presupuesto
from .models import PerfilUsuario


def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_completo', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        confirmacion = request.POST.get('password_confirmacion', '')

        if not all([nombre, correo, password, confirmacion]):
            messages.error(request, 'Todos los campos son obligatorios.')
        elif password != confirmacion:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif User.objects.filter(username=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
        else:
            try:
                validate_password(password)
            except ValidationError as error:
                for mensaje in error.messages:
                    messages.error(request, mensaje)
            else:
                usuario = User.objects.create_user(
                    username=correo,
                    email=correo,
                    password=password,
                )
                PerfilUsuario.objects.create(
                    usuario=usuario,
                    nombre_completo=nombre,
                )
                login(request, usuario)
                messages.success(request, 'Cuenta creada correctamente. Bienvenido.')
                return redirect('inicio')

    return render(request, 'usuarios/registro.html')


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        usuario = authenticate(request, username=correo, password=password)

        if usuario is not None:
            login(request, usuario)
            return redirect('inicio')

        messages.error(request, 'El correo o la contraseña no son correctos.')

    return render(request, 'usuarios/login.html')


def cerrar_sesion(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required
def inicio(request):
    usuario = request.user
    fecha = timezone.localdate()
    mes = fecha.month
    anio = fecha.year

    ingresos = Ingreso.objects.filter(usuario=usuario)
    gastos = Gasto.objects.filter(usuario=usuario)
    pendientes = GastoPendiente.objects.filter(usuario=usuario, estado='pendiente')

    total_ingresos = ingresos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    total_pendientes = pendientes.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    disponible = total_ingresos - total_gastos - total_pendientes

    ingresos_mes = ingresos.filter(fecha__month=mes, fecha__year=anio).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    gastos_mes = gastos.filter(fecha__month=mes, fecha__year=anio).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    pendientes_mes = pendientes.filter(fecha_limite__month=mes, fecha_limite__year=anio).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    disponible_mes = ingresos_mes - gastos_mes - pendientes_mes

    presupuestos = Presupuesto.objects.filter(
        usuario=usuario,
        mes=mes,
        anio=anio,
    ).select_related('categoria')

    total_presupuesto = Decimal('0.00')
    total_gastado_presupuesto = Decimal('0.00')
    alertas = []
    for presupuesto in presupuestos:
        gastado = gastos.filter(
            categoria=presupuesto.categoria,
            fecha__month=mes,
            fecha__year=anio,
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        restante = presupuesto.monto - gastado
        porcentaje = (gastado / presupuesto.monto * Decimal('100')) if presupuesto.monto else Decimal('0')
        presupuesto.gastado = gastado
        presupuesto.restante = restante
        presupuesto.porcentaje = porcentaje
        total_presupuesto += presupuesto.monto
        total_gastado_presupuesto += gastado
        if restante < 0:
            alertas.append({'categoria': presupuesto.categoria.nombre, 'estado': 'superado', 'mensaje': 'El gasto supera el presupuesto establecido.'})
        elif porcentaje >= 80:
            alertas.append({'categoria': presupuesto.categoria.nombre, 'estado': 'precaucion', 'mensaje': 'El gasto está cerca del límite mensual.'})

    porcentaje_presupuesto = (
        total_gastado_presupuesto / total_presupuesto * Decimal('100')
        if total_presupuesto else Decimal('0')
    )

    if total_ingresos == 0 and total_gastos == 0 and total_pendientes == 0:
        estado = 'Sin movimientos'
        mensaje = 'Registra tus ingresos y gastos para comenzar a analizar tu situación financiera.'
    elif disponible < 0:
        estado = 'Situación de riesgo'
        mensaje = 'Los gastos y compromisos pendientes superan los ingresos disponibles.'
    elif disponible == 0:
        estado = 'Sin saldo disponible'
        mensaje = 'Los ingresos están completamente comprometidos entre gastos y pagos pendientes.'
    elif total_ingresos > 0 and ((total_gastos + total_pendientes) / total_ingresos) >= Decimal('0.80'):
        estado = 'Precaución'
        mensaje = 'Una parte importante de los ingresos ya está comprometida. Conviene controlar los próximos gastos.'
    else:
        estado = 'Situación estable'
        mensaje = 'Los ingresos superan los gastos y compromisos pendientes. Se recomienda mantener el control financiero.'

    meta = MetaAhorro.objects.filter(usuario=usuario).order_by('estado', 'fecha_objetivo', '-fecha_registro').first()
    porcentaje_meta = Decimal('0')
    if meta and meta.monto_objetivo > 0:
        porcentaje_meta = min(Decimal('100'), meta.monto_actual / meta.monto_objetivo * Decimal('100'))

    nombres_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    return render(request, 'usuarios/inicio.html', {
        'perfil': getattr(usuario, 'perfil', None),
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_gastos_pendientes': total_pendientes,
        'dinero_disponible': disponible,
        'ingresos_mes_total': ingresos_mes,
        'gastos_mes_total': gastos_mes,
        'total_gastos_pendientes_mes': pendientes_mes,
        'disponible_mes': disponible_mes,
        'presupuestos': presupuestos,
        'total_presupuesto': total_presupuesto,
        'total_gastado_presupuestado': total_gastado_presupuesto,
        'total_restante_presupuesto': total_presupuesto - total_gastado_presupuesto,
        'porcentaje_presupuesto': porcentaje_presupuesto,
        'alertas_presupuesto': alertas,
        'estado_financiero': estado,
        'mensaje_financiero': mensaje,
        'ultimos_ingresos': ingresos.order_by('-fecha', '-id')[:5],
        'ultimos_gastos': gastos.select_related('categoria').order_by('-fecha', '-id')[:5],
        'meta_ahorro_principal': meta,
        'porcentaje_meta_ahorro': porcentaje_meta,
        'mes_actual': nombres_meses[mes - 1],
        'anio_actual': anio,
    })

def recuperar_password(request):
    vista = PasswordResetView.as_view(
        template_name='usuarios/recuperar_password.html',
        email_template_name='usuarios/password_reset_email.html',
        subject_template_name='usuarios/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    )
    return vista(request)
