from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.finanzas.models import Categoria, Gasto
from .models import Presupuesto


def _decimal(value):
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _categorias(usuario):
    return (Categoria.objects.filter(usuario__isnull=True) | Categoria.objects.filter(usuario=usuario)).order_by('nombre')


@login_required
def lista_presupuestos(request):
    qs = Presupuesto.objects.filter(usuario=request.user).select_related('categoria')

    anio = request.GET.get('anio', '').strip()
    mes = request.GET.get('mes', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    estado = request.GET.get('estado', '').strip()

    if anio.isdigit():
        qs = qs.filter(anio=int(anio))
    if mes.isdigit() and 1 <= int(mes) <= 12:
        qs = qs.filter(mes=int(mes))
    if categoria_id.isdigit():
        qs = qs.filter(categoria_id=int(categoria_id))

    presupuestos = []
    for presupuesto in qs.order_by('-anio', '-mes', 'categoria__nombre'):
        gastado = Gasto.objects.filter(
            usuario=request.user,
            categoria=presupuesto.categoria,
            fecha__month=presupuesto.mes,
            fecha__year=presupuesto.anio,
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        restante = presupuesto.monto - gastado
        porcentaje = (gastado / presupuesto.monto * Decimal('100')) if presupuesto.monto else Decimal('0')

        if restante < 0:
            estado_calculado = 'superado'
        elif porcentaje >= 80:
            estado_calculado = 'precaucion'
        else:
            estado_calculado = 'en_control'

        if estado and estado != estado_calculado:
            continue

        presupuesto.gastado = gastado
        presupuesto.restante = restante
        presupuesto.porcentaje = porcentaje
        presupuesto.estado_calculado = estado_calculado
        presupuestos.append(presupuesto)

    return render(request, 'presupuesto/lista.html', {
        'presupuestos': presupuestos,
        'categorias': _categorias(request.user),
        'filtros': request.GET,
    })


@login_required
def registrar_presupuesto(request):
    categorias = _categorias(request.user)
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria', '').strip()
        monto = _decimal(request.POST.get('monto', '').strip())
        mes = request.POST.get('mes', '').strip()
        anio = request.POST.get('anio', '').strip()

        categoria = None
        if categoria_id.isdigit():
            categoria = get_object_or_404(Categoria, id=int(categoria_id))

        if categoria is None or monto is None or monto <= 0 or not mes or not anio:
            messages.error(request, 'Complete correctamente todos los campos.')
        elif categoria.usuario_id not in {None, request.user.id}:
            messages.error(request, 'No tienes permiso para utilizar esa categoría.')
        else:
            try:
                mes_int = int(mes)
                anio_int = int(anio)
            except ValueError:
                mes_int, anio_int = 0, 0

            if not 1 <= mes_int <= 12 or not 2000 <= anio_int <= 2100:
                messages.error(request, 'El mes o el año no son válidos.')
            else:
                presupuesto, creado = Presupuesto.objects.update_or_create(
                    usuario=request.user,
                    categoria=categoria,
                    mes=mes_int,
                    anio=anio_int,
                    defaults={'monto': monto},
                )
                messages.success(
                    request,
                    'Presupuesto registrado correctamente.' if creado else 'Presupuesto actualizado correctamente.'
                )
                return redirect('lista_presupuestos')

    return render(request, 'presupuesto/registrar.html', {'categorias': categorias})


@login_required
def editar_presupuesto(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id, usuario=request.user)
    categorias = _categorias(request.user)

    if request.method == 'POST':
        categoria_id = request.POST.get('categoria', '').strip()
        monto = _decimal(request.POST.get('monto', '').strip())
        mes = request.POST.get('mes', '').strip()
        anio = request.POST.get('anio', '').strip()
        categoria = get_object_or_404(Categoria, id=int(categoria_id)) if categoria_id.isdigit() else None

        try:
            mes_int = int(mes)
            anio_int = int(anio)
        except ValueError:
            mes_int, anio_int = 0, 0

        duplicado = Presupuesto.objects.filter(
            usuario=request.user,
            categoria=categoria,
            mes=mes_int,
            anio=anio_int,
        ).exclude(id=presupuesto.id).exists() if categoria else False

        if categoria is None or monto is None or monto <= 0 or not (1 <= mes_int <= 12) or not (2000 <= anio_int <= 2100):
            messages.error(request, 'Complete correctamente todos los campos.')
        elif categoria.usuario_id not in {None, request.user.id}:
            messages.error(request, 'No tienes permiso para utilizar esa categoría.')
        elif duplicado:
            messages.error(request, 'Ya existe un presupuesto para esa categoría y periodo.')
        else:
            presupuesto.categoria = categoria
            presupuesto.monto = monto
            presupuesto.mes = mes_int
            presupuesto.anio = anio_int
            presupuesto.save()
            messages.success(request, 'Presupuesto actualizado correctamente.')
            return redirect('lista_presupuestos')

    return render(request, 'presupuesto/editar.html', {
        'presupuesto': presupuesto,
        'categorias': categorias,
    })


@login_required
def eliminar_presupuesto(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id, usuario=request.user)
    if request.method == 'POST':
        presupuesto.delete()
        messages.success(request, 'Presupuesto eliminado correctamente.')
        return redirect('lista_presupuestos')
    return render(request, 'presupuesto/eliminar.html', {'presupuesto': presupuesto})
