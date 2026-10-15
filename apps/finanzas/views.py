from decimal import Decimal, InvalidOperation
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.utils import timezone

from .models import Categoria, Gasto, GastoPendiente, Ingreso, MetaAhorro


def _decimal(value):
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _categorias_disponibles(usuario):
    return Categoria.objects.filter(
        Q(usuario__isnull=True) | Q(usuario=usuario)
    ).order_by('nombre')


# ============================================================
# INGRESOS
# ============================================================

@login_required
def lista_ingresos(request):
    ingresos = Ingreso.objects.filter(usuario=request.user)

    fecha_desde = request.GET.get('desde', '').strip()
    fecha_hasta = request.GET.get('hasta', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    minimo = request.GET.get('minimo', '').strip()
    maximo = request.GET.get('maximo', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    if fecha_desde:
        ingresos = ingresos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        ingresos = ingresos.filter(fecha__lte=fecha_hasta)
    if tipo in {'fijo', 'variable'}:
        ingresos = ingresos.filter(tipo=tipo)
    if buscar:
        ingresos = ingresos.filter(descripcion__icontains=buscar)

    minimo_decimal = _decimal(minimo) if minimo else None
    maximo_decimal = _decimal(maximo) if maximo else None
    if minimo_decimal is not None:
        ingresos = ingresos.filter(monto__gte=minimo_decimal)
    if maximo_decimal is not None:
        ingresos = ingresos.filter(monto__lte=maximo_decimal)

    ingresos = ingresos.order_by('-fecha', '-id')
    total = ingresos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    return render(request, 'finanzas/ingresos.html', {
        'ingresos': ingresos,
        'total_ingresos': total,
        'filtros': request.GET,
    })


@login_required
def registrar_ingreso(request):
    datos = {
        'descripcion': request.POST.get('descripcion', '').strip(),
        'monto': request.POST.get('monto', '').strip(),
        'fecha': request.POST.get('fecha', '').strip(),
        'tipo': request.POST.get('tipo', 'variable'),
    }

    if request.method == 'POST':
        monto = _decimal(datos['monto'])
        if not all([datos['descripcion'], datos['monto'], datos['fecha']]):
            messages.error(request, 'Todos los campos son obligatorios.')
        elif monto is None or monto <= 0:
            messages.error(request, 'El monto debe ser un valor válido mayor que cero.')
        elif datos['tipo'] not in {'fijo', 'variable'}:
            messages.error(request, 'El tipo de ingreso seleccionado no es válido.')
        else:
            Ingreso.objects.create(
                usuario=request.user,
                descripcion=datos['descripcion'],
                monto=monto,
                fecha=datos['fecha'],
                tipo=datos['tipo'],
            )
            messages.success(request, 'Ingreso registrado correctamente.')
            return redirect('lista_ingresos')

    return render(request, 'finanzas/registrar_ingreso.html', {'datos': datos})


@login_required
def editar_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id, usuario=request.user)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        monto = _decimal(request.POST.get('monto', '').strip())
        fecha = request.POST.get('fecha', '').strip()
        tipo = request.POST.get('tipo', 'variable')

        if not descripcion or not fecha or monto is None or monto <= 0:
            messages.error(request, 'Complete correctamente todos los campos.')
        elif tipo not in {'fijo', 'variable'}:
            messages.error(request, 'El tipo de ingreso no es válido.')
        else:
            ingreso.descripcion = descripcion
            ingreso.monto = monto
            ingreso.fecha = fecha
            ingreso.tipo = tipo
            ingreso.save(update_fields=['descripcion', 'monto', 'fecha', 'tipo'])
            messages.success(request, 'Ingreso actualizado correctamente.')
            return redirect('lista_ingresos')

    return render(request, 'finanzas/editar_ingreso.html', {'ingreso': ingreso})


@login_required
def eliminar_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id, usuario=request.user)
    if request.method == 'POST':
        ingreso.delete()
        messages.success(request, 'Ingreso eliminado correctamente.')
        return redirect('lista_ingresos')
    return render(request, 'finanzas/eliminar_ingreso.html', {'ingreso': ingreso})


# ============================================================
# GASTOS
# ============================================================

@login_required
def lista_gastos(request):
    gastos = Gasto.objects.filter(usuario=request.user).select_related('categoria')

    fecha_desde = request.GET.get('desde', '').strip()
    fecha_hasta = request.GET.get('hasta', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    minimo = request.GET.get('minimo', '').strip()
    maximo = request.GET.get('maximo', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    if fecha_desde:
        gastos = gastos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        gastos = gastos.filter(fecha__lte=fecha_hasta)
    if categoria_id.isdigit():
        gastos = gastos.filter(categoria_id=int(categoria_id))
    if tipo in {'fijo', 'variable'}:
        gastos = gastos.filter(tipo=tipo)
    if buscar:
        gastos = gastos.filter(descripcion__icontains=buscar)

    minimo_decimal = _decimal(minimo) if minimo else None
    maximo_decimal = _decimal(maximo) if maximo else None
    if minimo_decimal is not None:
        gastos = gastos.filter(monto__gte=minimo_decimal)
    if maximo_decimal is not None:
        gastos = gastos.filter(monto__lte=maximo_decimal)

    gastos = gastos.order_by('-fecha', '-id')
    total = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    return render(request, 'finanzas/gastos.html', {
        'gastos': gastos,
        'total_gastos': total,
        'categorias': _categorias_disponibles(request.user),
        'filtros': request.GET,
    })


@login_required
def registrar_gasto(request):
    categorias = _categorias_disponibles(request.user)
    datos = {
        'descripcion': request.POST.get('descripcion', '').strip(),
        'monto': request.POST.get('monto', '').strip(),
        'fecha': request.POST.get('fecha', '').strip(),
        'tipo': request.POST.get('tipo', 'variable'),
        'categoria': request.POST.get('categoria', '').strip(),
        'nueva_categoria': request.POST.get('nueva_categoria', '').strip(),
    }

    if request.method == 'POST':
        monto = _decimal(datos['monto'])
        categoria = None
        valido = True

        if not all([datos['descripcion'], datos['monto'], datos['fecha']]):
            messages.error(request, 'Todos los campos son obligatorios.')
            valido = False
        elif monto is None or monto <= 0:
            messages.error(request, 'El monto debe ser un valor válido mayor que cero.')
            valido = False
        elif datos['tipo'] not in {'fijo', 'variable'}:
            messages.error(request, 'El tipo de gasto no es válido.')
            valido = False
        elif datos['categoria'] == 'nueva':
            if not datos['nueva_categoria']:
                messages.error(request, 'Ingrese el nombre de la nueva categoría.')
                valido = False
            else:
                categoria = Categoria.objects.filter(
                    nombre__iexact=datos['nueva_categoria'],
                    usuario=request.user,
                ).first()
                if categoria is None:
                    categoria = Categoria.objects.create(
                        nombre=datos['nueva_categoria'],
                        usuario=request.user,
                    )
        elif datos['categoria'].isdigit():
            categoria = get_object_or_404(Categoria, id=int(datos['categoria']))
            if categoria.usuario_id not in {None, request.user.id}:
                messages.error(request, 'No tienes permiso para utilizar esa categoría.')
                valido = False
        else:
            messages.error(request, 'Debe seleccionar una categoría.')
            valido = False

        if valido and categoria is not None:
            Gasto.objects.create(
                usuario=request.user,
                categoria=categoria,
                descripcion=datos['descripcion'],
                monto=monto,
                fecha=datos['fecha'],
                tipo=datos['tipo'],
            )
            messages.success(request, 'Gasto registrado correctamente.')
            return redirect('lista_gastos')

    return render(request, 'finanzas/registrar_gasto.html', {
        'categorias': categorias,
        'datos': datos,
    })


@login_required
def editar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id, usuario=request.user)
    categorias = _categorias_disponibles(request.user)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        monto = _decimal(request.POST.get('monto', '').strip())
        fecha = request.POST.get('fecha', '').strip()
        tipo = request.POST.get('tipo', 'variable')
        categoria_id = request.POST.get('categoria', '').strip()

        categoria = None
        if categoria_id.isdigit():
            categoria = get_object_or_404(Categoria, id=int(categoria_id))

        if not descripcion or not fecha or monto is None or monto <= 0 or categoria is None:
            messages.error(request, 'Complete correctamente todos los campos.')
        elif categoria.usuario_id not in {None, request.user.id}:
            messages.error(request, 'No tienes permiso para utilizar esa categoría.')
        elif tipo not in {'fijo', 'variable'}:
            messages.error(request, 'El tipo de gasto no es válido.')
        else:
            gasto.descripcion = descripcion
            gasto.monto = monto
            gasto.fecha = fecha
            gasto.tipo = tipo
            gasto.categoria = categoria
            gasto.save(update_fields=['descripcion', 'monto', 'fecha', 'tipo', 'categoria'])
            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect('lista_gastos')

    return render(request, 'finanzas/editar_gasto.html', {
        'gasto': gasto,
        'categorias': categorias,
    })


@login_required
def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id, usuario=request.user)
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto eliminado correctamente.')
        return redirect('lista_gastos')
    return render(request, 'finanzas/eliminar_gasto.html', {'gasto': gasto})


# ============================================================
# GASTOS PENDIENTES
# ============================================================

@login_required
def lista_gastos_pendientes(request):
    gastos = GastoPendiente.objects.filter(usuario=request.user).select_related('categoria')

    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    estado = request.GET.get('estado', '').strip()
    minimo = request.GET.get('minimo', '').strip()
    maximo = request.GET.get('maximo', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    if desde:
        gastos = gastos.filter(fecha_limite__gte=desde)
    if hasta:
        gastos = gastos.filter(fecha_limite__lte=hasta)
    if estado in {'pendiente', 'completado'}:
        gastos = gastos.filter(estado=estado)
    if buscar:
        gastos = gastos.filter(descripcion__icontains=buscar)

    minimo_decimal = _decimal(minimo) if minimo else None
    maximo_decimal = _decimal(maximo) if maximo else None
    if minimo_decimal is not None:
        gastos = gastos.filter(monto__gte=minimo_decimal)
    if maximo_decimal is not None:
        gastos = gastos.filter(monto__lte=maximo_decimal)

    gastos = gastos.order_by('estado', 'fecha_limite', '-id')
    return render(request, 'finanzas/gastos_pendientes.html', {
        'gastos_pendientes': gastos,
        'categorias': _categorias_disponibles(request.user),
        'filtros': request.GET,
    })


@login_required
def registrar_gasto_pendiente(request):
    categorias = _categorias_disponibles(request.user)
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        monto = _decimal(request.POST.get('monto', '').strip())
        fecha_limite = request.POST.get('fecha_limite', '').strip()
        categoria_id = request.POST.get('categoria', '').strip()

        categoria = None
        if categoria_id.isdigit():
            categoria = get_object_or_404(Categoria, id=int(categoria_id))

        if not descripcion or monto is None or monto <= 0 or not fecha_limite:
            messages.error(request, 'Complete correctamente todos los campos.')
        elif categoria is not None and categoria.usuario_id not in {None, request.user.id}:
            messages.error(request, 'No tienes permiso para utilizar esa categoría.')
        else:
            GastoPendiente.objects.create(
                usuario=request.user,
                categoria=categoria,
                descripcion=descripcion,
                monto=monto,
                fecha_limite=fecha_limite,
            )
            messages.success(request, 'Gasto pendiente registrado correctamente.')
            return redirect('lista_gastos_pendientes')

    return render(request, 'finanzas/registrar_gasto_pendiente.html', {
        'categorias': categorias,
    })


@login_required
def completar_gasto_pendiente(request, gasto_pendiente_id):
    gasto_pendiente = get_object_or_404(
        GastoPendiente,
        id=gasto_pendiente_id,
        usuario=request.user,
    )
    categorias = _categorias_disponibles(request.user)

    if gasto_pendiente.estado == 'completado':
        messages.info(request, 'Este gasto pendiente ya fue completado.')
        return redirect('lista_gastos_pendientes')

    if request.method == 'POST':
        categoria_id = request.POST.get('categoria', '').strip()
        categoria = gasto_pendiente.categoria

        if categoria_id.isdigit():
            categoria = get_object_or_404(
                Categoria,
                id=int(categoria_id),
            )

        if categoria is None:
            messages.error(
                request,
                'Seleccione una categoría antes de completar el gasto.'
            )
        elif categoria.usuario_id not in {None, request.user.id}:
            messages.error(
                request,
                'No tiene permiso para utilizar la categoría seleccionada.'
            )
        else:
            with transaction.atomic():
                Gasto.objects.create(
                    usuario=request.user,
                    categoria=categoria,
                    descripcion=gasto_pendiente.descripcion,
                    monto=gasto_pendiente.monto,
                    fecha=gasto_pendiente.fecha_limite,
                    tipo='variable',
                )
                gasto_pendiente.categoria = categoria
                gasto_pendiente.estado = 'completado'
                gasto_pendiente.save(update_fields=['categoria', 'estado'])

            messages.success(
                request,
                'El gasto pendiente fue completado y registrado correctamente como gasto.'
            )
            return redirect('lista_gastos_pendientes')

    return render(request, 'finanzas/confirmar_gasto_pendiente.html', {
        'gasto_pendiente': gasto_pendiente,
        'categorias': categorias,
    })


@login_required
def eliminar_gasto_pendiente(request, gasto_pendiente_id):
    gasto = get_object_or_404(
        GastoPendiente,
        id=gasto_pendiente_id,
        usuario=request.user,
    )
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto pendiente eliminado correctamente.')
        return redirect('lista_gastos_pendientes')
    return render(request, 'finanzas/eliminar_gasto_pendiente.html', {'gasto_pendiente': gasto})


# ============================================================
# METAS DE AHORRO
# ============================================================

@login_required
def lista_metas_ahorro(request):
    metas = MetaAhorro.objects.filter(usuario=request.user)
    estado = request.GET.get('estado', '').strip()
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    if estado in {'activa', 'completada'}:
        metas = metas.filter(estado=estado)
    if desde:
        metas = metas.filter(fecha_objetivo__gte=desde)
    if hasta:
        metas = metas.filter(fecha_objetivo__lte=hasta)
    if buscar:
        metas = metas.filter(nombre__icontains=buscar)

    metas = metas.order_by('estado', 'fecha_objetivo', '-fecha_registro')
    for meta in metas:
        if meta.monto_objetivo > 0:
            meta.porcentaje = min(
                Decimal('100'),
                (meta.monto_actual / meta.monto_objetivo) * Decimal('100'),
            )
        else:
            meta.porcentaje = Decimal('0')

    return render(request, 'finanzas/metas_ahorro.html', {
        'metas': metas,
        'filtros': request.GET,
    })


@login_required
def registrar_meta_ahorro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        objetivo = _decimal(request.POST.get('monto_objetivo', '').strip())
        fecha_objetivo = request.POST.get('fecha_objetivo', '').strip() or None

        if not nombre or objetivo is None or objetivo <= 0:
            messages.error(request, 'Complete correctamente los datos de la meta.')
        else:
            MetaAhorro.objects.create(
                usuario=request.user,
                nombre=nombre,
                monto_objetivo=objetivo,
                fecha_objetivo=fecha_objetivo,
            )
            messages.success(request, 'Meta de ahorro creada correctamente.')
            return redirect('lista_metas_ahorro')

    return render(request, 'finanzas/registrar_meta_ahorro.html')


@login_required
def agregar_ahorro_meta(request, meta_id):
    meta = get_object_or_404(MetaAhorro, id=meta_id, usuario=request.user)
    if request.method == 'POST':
        monto = _decimal(request.POST.get('monto', '').strip())
        if monto is None or monto <= 0:
            messages.error(request, 'El monto debe ser mayor que cero.')
        else:
            meta.monto_actual = min(meta.monto_objetivo, meta.monto_actual + monto)
            if meta.monto_actual >= meta.monto_objetivo:
                meta.estado = 'completada'
            meta.save(update_fields=['monto_actual', 'estado'])
            messages.success(request, 'Ahorro agregado correctamente.')
    return redirect('lista_metas_ahorro')


@login_required
def completar_meta_ahorro(request, meta_id):
    meta = get_object_or_404(MetaAhorro, id=meta_id, usuario=request.user)
    if request.method == 'POST':
        meta.estado = 'completada'
        meta.monto_actual = meta.monto_objetivo
        meta.save(update_fields=['estado', 'monto_actual'])
        messages.success(request, 'Meta marcada como completada.')
    return redirect('lista_metas_ahorro')


@login_required
def eliminar_meta_ahorro(request, meta_id):
    meta = get_object_or_404(MetaAhorro, id=meta_id, usuario=request.user)
    if request.method == 'POST':
        meta.delete()
        messages.success(request, 'Meta de ahorro eliminada correctamente.')
    return redirect('lista_metas_ahorro')


# ============================================================
# HISTORIAL
# ============================================================

def _pdf_escape(value):
    return str(value).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _crear_pdf_historial(movimientos, usuario, periodo, total_ingresos, total_gastos):
    """Crea un PDF A4 horizontal con columnas alineadas y saltos de página."""
    from textwrap import shorten

    page_w, page_h = 842, 595  # A4 horizontal en puntos
    left, right = 36, 806
    rows_per_page = 25
    chunks = [movimientos[i:i + rows_per_page] for i in range(0, len(movimientos), rows_per_page)] or [[]]
    objects = []

    def add_object(content):
        if isinstance(content, str):
            content = content.encode('latin-1', errors='replace')
        objects.append(content)
        return len(objects)

    catalog_id = add_object(b'')
    pages_id = add_object(b'')
    font_id = add_object('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    page_ids = []
    for page_index, chunk in enumerate(chunks, start=1):
        cmds = []
        def text(x, y, value, size=9, bold=False):
            font = '/F2' if bold else '/F1'
            cmds.append(f'BT {font} {size} Tf {x} {y} Td ({_pdf_escape(value)}) Tj ET')
        text(left, 558, 'FINANZAS PERSONALES - HISTORIAL FINANCIERO', 16, True)
        text(left, 540, f'Usuario: {getattr(usuario, "email", "") or usuario.username}', 9)
        text(left, 525, f'Periodo: {periodo}', 9)
        text(450, 540, f'Ingresos: Bs {total_ingresos:,.2f}', 10, True)
        text(450, 525, f'Gastos: Bs {total_gastos:,.2f}', 10, True)
        text(650, 525, f'Balance: Bs {(total_ingresos-total_gastos):,.2f}', 10, True)
        # Table headings and separators
        headers = [(left, 'FECHA'), (112, 'TIPO'), (174, 'DESCRIPCION'), (410, 'CATEGORIA'), (550, 'CLASE'), (650, 'MONTO (Bs)')]
        cmds.append('0.75 w 0.65 G 36 507 m 806 507 l S')
        for x, label in headers:
            text(x, 490, label, 9, True)
        cmds.append('0.75 w 0.65 G 36 480 m 806 480 l S')
        y = 462
        for item in chunk:
            fecha = item['fecha'].strftime('%d/%m/%Y') if hasattr(item['fecha'], 'strftime') else str(item['fecha'])
            desc = shorten(str(item['descripcion']), width=37, placeholder='…')
            categoria = shorten(str(item['categoria'] or '—'), width=21, placeholder='…')
            clase = shorten(str(item['tipo_detalle']), width=14, placeholder='…')
            text(left, y, fecha, 8)
            text(112, y, item['tipo'], 8)
            text(174, y, desc, 8)
            text(410, y, categoria, 8)
            text(550, y, clase, 8)
            amount = f"{item['monto']:,.2f}"
            text(720, y, amount, 8)
            cmds.append(f'0.5 w 0.88 G 36 {y-6} m 806 {y-6} l S')
            y -= 15
        if not movimientos:
            text(left, y, 'No se encontraron movimientos para los filtros seleccionados.', 9)
        text(left, 24, f'Movimientos: {len(movimientos)}   |   Página {page_index} de {len(chunks)}', 8)
        stream = '\n'.join(cmds).encode('cp1252', errors='replace')
        stream_id = add_object(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')
        page_id = add_object(f'<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_w} {page_h}] /Resources << /Font << /F1 {font_id} 0 R /F2 {font_id} 0 R >> >> /Contents {stream_id} 0 R >>')
        page_ids.append(page_id)
    objects[catalog_id-1] = f'<< /Type /Catalog /Pages {pages_id} 0 R >>'.encode()
    objects[pages_id-1] = f'<< /Type /Pages /Kids [{" ".join(f"{pid} 0 R" for pid in page_ids)}] /Count {len(page_ids)} >>'.encode()
    pdf = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets=[0]
    for i,obj in enumerate(objects, start=1):
        offsets.append(len(pdf)); pdf.extend(f'{i} 0 obj\n'.encode()); pdf.extend(obj); pdf.extend(b'\nendobj\n')
    xref=len(pdf); pdf.extend(f'xref\n0 {len(objects)+1}\n'.encode()); pdf.extend(b'0000000000 65535 f \n')
    for off in offsets[1:]: pdf.extend(f'{off:010d} 00000 n \n'.encode())
    pdf.extend(f'trailer\n<< /Size {len(objects)+1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())
    return bytes(pdf)


def _crear_excel_historial(movimientos, usuario, periodo, total_ingresos, total_gastos):
    """Genera un .xlsx válido sin dependencias externas, usando XML de Excel."""
    import zipfile
    from xml.sax.saxutils import escape
    from io import BytesIO

    def col_name(n):
        result = ''
        while n:
            n, rem = divmod(n - 1, 26)
            result = chr(65 + rem) + result
        return result

    rows = [
        ['FINANZAS PERSONALES - HISTORIAL FINANCIERO'],
        ['Usuario', getattr(usuario, 'email', '') or usuario.username],
        ['Periodo', periodo],
        ['Total de ingresos (Bs)', float(total_ingresos)],
        ['Total de gastos (Bs)', float(total_gastos)],
        ['Balance del periodo (Bs)', float(total_ingresos-total_gastos)],
        [],
        ['Fecha', 'Tipo', 'Descripción', 'Categoría', 'Clase', 'Monto (Bs)'],
    ]
    for item in movimientos:
        fecha = item['fecha'].strftime('%d/%m/%Y') if hasattr(item['fecha'], 'strftime') else str(item['fecha'])
        rows.append([fecha, item['tipo'], item['descripcion'], item['categoria'] or '—', item['tipo_detalle'], float(item['monto'])])
    xml_rows=[]
    for ri,row in enumerate(rows, start=1):
        cells=[]
        for ci,value in enumerate(row, start=1):
            if value is None or value == '': continue
            ref=f'{col_name(ci)}{ri}'
            if isinstance(value, (int,float)) and not isinstance(value,bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>')
        xml_rows.append(f'<row r="{ri}">{"".join(cells)}</row>')
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"/></sheetViews><cols><col min="1" max="1" width="15" customWidth="1"/><col min="2" max="2" width="18" customWidth="1"/><col min="3" max="3" width="36" customWidth="1"/><col min="4" max="4" width="22" customWidth="1"/><col min="5" max="5" width="16" customWidth="1"/><col min="6" max="6" width="16" customWidth="1"/></cols><sheetData>' + ''.join(xml_rows) + '</sheetData></worksheet>')
    workbook='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Historial" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    wb_rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    types='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    out=BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',types)
        z.writestr('_rels/.rels',rels)
        z.writestr('xl/workbook.xml',workbook)
        z.writestr('xl/_rels/workbook.xml.rels',wb_rels)
        z.writestr('xl/worksheets/sheet1.xml',sheet)
    return out.getvalue()


@login_required
def historial(request):
    ingresos = Ingreso.objects.filter(usuario=request.user)
    gastos = Gasto.objects.filter(usuario=request.user).select_related('categoria')

    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    tipo_movimiento = request.GET.get('tipo', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    minimo = request.GET.get('minimo', '').strip()
    maximo = request.GET.get('maximo', '').strip()
    buscar = request.GET.get('buscar', '').strip()
    ordenar = request.GET.get('ordenar', 'recientes').strip()
    hoy = timezone.localdate()
    mes_actual = request.GET.get('mes', str(hoy.month)).strip()
    anio_actual = request.GET.get('anio', str(hoy.year)).strip()

    try:
        mes_num = int(mes_actual)
        if not 1 <= mes_num <= 12:
            mes_num = hoy.month
    except (TypeError, ValueError):
        mes_num = hoy.month
    try:
        anio_num = int(anio_actual)
        if not 2000 <= anio_num <= 2100:
            anio_num = hoy.year
    except (TypeError, ValueError):
        anio_num = hoy.year

    # El mes y año forman el periodo principal; las fechas opcionales afinan la consulta.
    desde_periodo = date(anio_num, mes_num, 1)
    hasta_periodo = date(anio_num + (mes_num == 12), 1 if mes_num == 12 else mes_num + 1, 1)
    hasta_periodo = date.fromordinal(hasta_periodo.toordinal() - 1)
    ingresos = ingresos.filter(fecha__gte=desde_periodo, fecha__lte=hasta_periodo)
    gastos = gastos.filter(fecha__gte=desde_periodo, fecha__lte=hasta_periodo)
    if desde:
        ingresos = ingresos.filter(fecha__gte=desde)
        gastos = gastos.filter(fecha__gte=desde)
    if hasta:
        ingresos = ingresos.filter(fecha__lte=hasta)
        gastos = gastos.filter(fecha__lte=hasta)

    movimientos = []
    min_d = _decimal(minimo) if minimo else None
    max_d = _decimal(maximo) if maximo else None

    if tipo_movimiento in {'', 'ingreso'}:
        qs = ingresos
        if buscar:
            qs = qs.filter(descripcion__icontains=buscar)
        if min_d is not None:
            qs = qs.filter(monto__gte=min_d)
        if max_d is not None:
            qs = qs.filter(monto__lte=max_d)
        for item in qs:
            movimientos.append({'fecha': item.fecha, 'tipo': 'Ingreso', 'descripcion': item.descripcion,
                                'categoria': '', 'tipo_detalle': item.get_tipo_display(), 'monto': item.monto})

    if tipo_movimiento in {'', 'gasto'}:
        qs = gastos
        if categoria_id.isdigit():
            qs = qs.filter(categoria_id=int(categoria_id))
        if buscar:
            qs = qs.filter(descripcion__icontains=buscar)
        if min_d is not None:
            qs = qs.filter(monto__gte=min_d)
        if max_d is not None:
            qs = qs.filter(monto__lte=max_d)
        for item in qs:
            movimientos.append({'fecha': item.fecha, 'tipo': 'Gasto', 'descripcion': item.descripcion,
                                'categoria': item.categoria.nombre if item.categoria else '',
                                'tipo_detalle': item.get_tipo_display(), 'monto': item.monto})

    if ordenar == 'antiguos':
        movimientos.sort(key=lambda x: x['fecha'])
    elif ordenar == 'mayor':
        movimientos.sort(key=lambda x: x['monto'], reverse=True)
    elif ordenar == 'menor':
        movimientos.sort(key=lambda x: x['monto'])
    else:
        movimientos.sort(key=lambda x: x['fecha'], reverse=True)

    total_ingresos = sum((m['monto'] for m in movimientos if m['tipo'] == 'Ingreso'), Decimal('0.00'))
    total_gastos = sum((m['monto'] for m in movimientos if m['tipo'] == 'Gasto'), Decimal('0.00'))
    meses = [(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
             (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')]
    anios = range(max(2020, hoy.year - 5), hoy.year + 3)
    periodo = f'{dict(meses)[mes_num]} de {anio_num}'

    if request.GET.get('exportar') == 'pdf':
        pdf = _crear_pdf_historial(movimientos, request.user, periodo, total_ingresos, total_gastos)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="historial_financiero_{anio_num}_{mes_num:02d}.pdf"'
        return response
    if request.GET.get('exportar') == 'excel':
        excel = _crear_excel_historial(movimientos, request.user, periodo, total_ingresos, total_gastos)
        response = HttpResponse(excel, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="historial_financiero_{anio_num}_{mes_num:02d}.xlsx"'
        return response

    return render(request, 'finanzas/historial.html', {
        'movimientos': movimientos,
        'categorias': _categorias_disponibles(request.user),
        'filtros': {'desde': desde, 'hasta': hasta, 'tipo': tipo_movimiento, 'categoria': categoria_id,
                    'minimo': minimo, 'maximo': maximo, 'buscar': buscar, 'ordenar': ordenar,
                    'mes': str(mes_num), 'anio': str(anio_num)},
        'meses': meses, 'anios': anios, 'mes_nombre': dict(meses)[mes_num],
        'total_ingresos': total_ingresos, 'total_gastos': total_gastos,
        'balance_periodo': total_ingresos - total_gastos,
    })
