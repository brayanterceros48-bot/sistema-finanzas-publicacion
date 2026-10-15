from decimal import Decimal, InvalidOperation
import re
import unicodedata

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.finanzas.models import Ingreso, Gasto, Categoria, GastoPendiente
from apps.presupuesto.models import Presupuesto


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(texto):
    """
    Convierte el texto a minúsculas y elimina tildes.
    """

    texto = texto.lower()

    texto = unicodedata.normalize(
        'NFD',
        texto
    )

    texto = ''.join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != 'Mn'
    )

    return texto


def convertir_monto(texto):
    """
    Convierte montos escritos en diferentes formatos.

    Ejemplos:

    1500       -> 1500
    1.500      -> 1500
    1,500      -> 1500
    1500.50    -> 1500.50
    1500,50    -> 1500.50
    1.500,50   -> 1500.50
    """

    texto = texto.strip()

    # --------------------------------------------------------
    # Formato con punto y coma
    # Ejemplo: 1.500,50
    # --------------------------------------------------------

    if '.' in texto and ',' in texto:

        texto = texto.replace('.', '')
        texto = texto.replace(',', '.')

        return Decimal(texto)

    # --------------------------------------------------------
    # Solo punto
    # --------------------------------------------------------

    if '.' in texto:

        partes = texto.split('.')

        # Ejemplo: 1.500
        # Se interpreta como mil quinientos.

        if (
            len(partes) == 2
            and len(partes[1]) == 3
            and partes[0].isdigit()
            and partes[1].isdigit()
        ):

            texto = texto.replace('.', '')

            return Decimal(texto)

        # Ejemplo: 1500.50

        return Decimal(texto)

    # --------------------------------------------------------
    # Solo coma
    # --------------------------------------------------------

    if ',' in texto:

        partes = texto.split(',')

        # Ejemplo: 1,500
        # Se interpreta como mil quinientos.

        if (
            len(partes) == 2
            and len(partes[1]) == 3
            and partes[0].isdigit()
            and partes[1].isdigit()
        ):

            texto = texto.replace(',', '')

            return Decimal(texto)

        # Ejemplo: 1500,50

        texto = texto.replace(',', '.')

        return Decimal(texto)

    # --------------------------------------------------------
    # Número sin separadores
    # --------------------------------------------------------

    return Decimal(texto)


def detectar_categoria(pregunta, usuario):
    """
    Intenta identificar la categoría relacionada
    con la pregunta del usuario.
    """

    pregunta_normalizada = normalizar_texto(
        pregunta
    )

    # --------------------------------------------------------
    # CATEGORÍAS REGISTRADAS
    # --------------------------------------------------------

    categorias = (
        Categoria.objects
        .filter(
            usuario__isnull=True
        )
        | Categoria.objects.filter(
            usuario=usuario
        )
    ).order_by('nombre')

    for categoria in categorias:

        nombre_normalizado = normalizar_texto(
            categoria.nombre
        )

        if nombre_normalizado in pregunta_normalizada:

            return categoria

    # --------------------------------------------------------
    # PALABRAS CLAVE
    # --------------------------------------------------------

    palabras_clave = {

        'Alimentación': [
            'comida',
            'alimento',
            'almuerzo',
            'desayuno',
            'cena',
            'supermercado',
            'mercado',
        ],

        'Vivienda': [
            'casa',
            'alquiler',
            'vivienda',
            'habitacion',
        ],

        'Transporte': [
            'transporte',
            'taxi',
            'gasolina',
            'combustible',
            'pasaje',
            'bus',
        ],

        'Servicios': [
            'luz',
            'agua',
            'internet',
            'telefono',
            'servicio',
        ],

        'Salud': [
            'medicina',
            'medicamento',
            'doctor',
            'consulta',
            'salud',
        ],

        'Educación': [
            'educacion',
            'universidad',
            'colegio',
            'curso',
            'libro',
            'estudio',
        ],

        'Entretenimiento': [
            'cine',
            'juego',
            'fiesta',
            'entretenimiento',
        ],

        'Compras': [
            'celular',
            'telefono',
            'computadora',
            'laptop',
            'ropa',
            'zapatos',
            'electrodomestico',
            'comprar',
        ],

        'Deudas': [
            'deuda',
            'prestamo',
            'cuota',
        ],

        'Mascotas': [
            'mascota',
            'perro',
            'gato',
            'animal',
        ],
    }

    for nombre_categoria, palabras in palabras_clave.items():

        for palabra in palabras:

            if palabra in pregunta_normalizada:

                categoria = (
                    Categoria.objects
                    .filter(
                        nombre__iexact=nombre_categoria,
                        usuario__isnull=True
                    )
                    .first()
                )

                if categoria:
                    return categoria

                categoria = (
                    Categoria.objects
                    .filter(
                        nombre__iexact=nombre_categoria,
                        usuario=usuario
                    )
                    .first()
                )

                if categoria:
                    return categoria

    return None


# ============================================================
# CONSULTA FINANCIERA
# ============================================================

@login_required
def consultar_decision(request):

    # --------------------------------------------------------
    # DATOS FINANCIEROS GENERALES
    # --------------------------------------------------------

    total_ingresos = (
        Ingreso.objects
        .filter(
            usuario=request.user
        )
        .aggregate(
            total=Sum('monto')
        )['total']
        or Decimal('0.00')
    )

    total_gastos = (
        Gasto.objects
        .filter(
            usuario=request.user
        )
        .aggregate(
            total=Sum('monto')
        )['total']
        or Decimal('0.00')
    )

    # --------------------------------------------------------
    # GASTOS PENDIENTES
    # --------------------------------------------------------

    gastos_pendientes = (
        GastoPendiente.objects
        .filter(
            usuario=request.user,
            estado='pendiente'
        )
    )

    total_gastos_pendientes = (
        gastos_pendientes
        .aggregate(
            total=Sum('monto')
        )['total']
        or Decimal('0.00')
    )

    # --------------------------------------------------------
    # DINERO DISPONIBLE REAL
    # --------------------------------------------------------

    dinero_disponible = (
        total_ingresos
        - total_gastos
        - total_gastos_pendientes
    )

    # --------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------

    pregunta = ''

    decision = None

    titulo_decision = None

    mensaje_decision = None

    # ========================================================
    # PROCESAR PREGUNTA
    # ========================================================

    if request.method == 'POST':

        pregunta = request.POST.get(
            'pregunta',
            ''
        ).strip()

        pregunta_minuscula = (
            pregunta.lower()
        )

        # ====================================================
        # VALIDAR PREGUNTA
        # ====================================================

        if not pregunta:

            decision = 'error'

            titulo_decision = (
                'Escribe una pregunta'
            )

            mensaje_decision = (
                'Para realizar un análisis financiero, '
                'escribe una pregunta o consulta.'
            )

        else:

            # =================================================
            # EXTRAER MONTO
            # =================================================

            montos = re.findall(
                r'(?:bs\.?\s*)?'
                r'(\d+(?:[.,]\d{1,3})*)',
                pregunta_minuscula
            )

            monto = None

            if montos:

                try:

                    monto_texto = montos[-1]

                    monto = convertir_monto(
                        monto_texto
                    )

                except InvalidOperation:

                    monto = None

            # =================================================
            # CONSULTA: DINERO DISPONIBLE
            # =================================================

            if (
                'cuánto tengo' in pregunta_minuscula
                or 'cuanto tengo' in pregunta_minuscula
                or 'cuánto dinero tengo' in pregunta_minuscula
                or 'cuanto dinero tengo' in pregunta_minuscula
                or 'dinero disponible' in pregunta_minuscula
                or 'saldo disponible' in pregunta_minuscula
                or 'cuánto me queda' in pregunta_minuscula
                or 'cuanto me queda' in pregunta_minuscula
                or 'cuál es mi saldo' in pregunta_minuscula
                or 'cual es mi saldo' in pregunta_minuscula
                or 'qué saldo tengo' in pregunta_minuscula
                or 'que saldo tengo' in pregunta_minuscula
                or 'cuánto dinero me queda' in pregunta_minuscula
                or 'cuanto dinero me queda' in pregunta_minuscula
            ):

                decision = 'verde'

                titulo_decision = (
                    'Dinero disponible'
                )

                mensaje_decision = (
                    'Actualmente tienes Bs '
                    + format(
                        dinero_disponible,
                        ',.2f'
                    )
                    + ' disponibles. '
                    + 'Tus ingresos registrados son Bs '
                    + format(
                        total_ingresos,
                        ',.2f'
                    )
                    + ' y tus gastos registrados son Bs '
                    + format(
                        total_gastos,
                        ',.2f'
                    )
                    + '.'
                )

            # =================================================
            # CONSULTA: GASTOS
            # =================================================

            elif (
                'en qué gasto' in pregunta_minuscula
                or 'en que gasto' in pregunta_minuscula
                or 'en qué estoy gastando' in pregunta_minuscula
                or 'en que estoy gastando' in pregunta_minuscula
                or 'dónde estoy gastando' in pregunta_minuscula
                or 'donde estoy gastando' in pregunta_minuscula
                or 'dónde gasto' in pregunta_minuscula
                or 'donde gasto' in pregunta_minuscula
                or 'estoy gastando mucho' in pregunta_minuscula
                or 'estoy gastando demasiado' in pregunta_minuscula
                or 'gasto demasiado' in pregunta_minuscula
                or 'gasto mucho' in pregunta_minuscula
                or 'mis gastos' in pregunta_minuscula
                or 'cuál es mi mayor gasto' in pregunta_minuscula
                or 'cual es mi mayor gasto' in pregunta_minuscula
                or 'dónde gasto más' in pregunta_minuscula
                or 'donde gasto mas' in pregunta_minuscula
            ):

                fecha_actual = timezone.localdate()

                gastos_por_categoria = (
                    Gasto.objects
                    .filter(
                        usuario=request.user,
                        fecha__month=fecha_actual.month,
                        fecha__year=fecha_actual.year
                    )
                    .values(
                        'categoria__nombre'
                    )
                    .annotate(
                        total=Sum('monto')
                    )
                    .order_by(
                        '-total'
                    )
                )

                if gastos_por_categoria:

                    principal = (
                        gastos_por_categoria[0]
                    )

                    categoria_nombre = (
                        principal[
                            'categoria__nombre'
                        ]
                        or 'Sin categoría'
                    )

                    categoria_total = (
                        principal['total']
                    )

                    presupuesto = None

                    if categoria_nombre != 'Sin categoría':

                        presupuesto = (
                            Presupuesto.objects
                            .filter(
                                usuario=request.user,
                                categoria__nombre=categoria_nombre,
                                mes=fecha_actual.month,
                                anio=fecha_actual.year
                            )
                            .first()
                        )

                    if presupuesto:

                        restante = (
                            presupuesto.monto
                            - categoria_total
                        )

                        if presupuesto.monto > Decimal('0'):

                            porcentaje_usado = (
                                categoria_total
                                / presupuesto.monto
                            ) * Decimal('100')

                        else:

                            porcentaje_usado = Decimal('100')

                        if restante < Decimal('0'):

                            decision = 'rojo'

                            titulo_decision = (
                                'Presupuesto superado'
                            )

                            mensaje_decision = (
                                'La categoría donde más dinero '
                                'has registrado este mes es '
                                + categoria_nombre
                                + ', con Bs '
                                + format(
                                    categoria_total,
                                    ',.2f'
                                )
                                + '. El presupuesto mensual '
                                + 'establecido es de Bs '
                                + format(
                                    presupuesto.monto,
                                    ',.2f'
                                )
                                + ' y has utilizado aproximadamente '
                                + format(
                                    porcentaje_usado,
                                    '.1f'
                                )
                                + '% del presupuesto. '
                                + 'El presupuesto ha sido superado '
                                + 'en Bs '
                                + format(
                                    abs(restante),
                                    ',.2f'
                                )
                                + '.'
                            )

                        elif porcentaje_usado >= Decimal('80'):

                            decision = 'amarillo'

                            titulo_decision = (
                                'Gasto cercano al límite'
                            )

                            mensaje_decision = (
                                'La categoría donde más dinero '
                                'has registrado este mes es '
                                + categoria_nombre
                                + ', con Bs '
                                + format(
                                    categoria_total,
                                    ',.2f'
                                )
                                + '. El presupuesto mensual es '
                                + 'de Bs '
                                + format(
                                    presupuesto.monto,
                                    ',.2f'
                                )
                                + ' y ya has utilizado aproximadamente '
                                + format(
                                    porcentaje_usado,
                                    '.1f'
                                )
                                + '% del presupuesto. '
                                + 'Quedan Bs '
                                + format(
                                    restante,
                                    ',.2f'
                                )
                                + ' disponibles dentro de esta '
                                + 'categoría. Conviene controlar '
                                + 'los próximos gastos.'
                            )

                        else:

                            decision = 'verde'

                            titulo_decision = (
                                'Gastos dentro del presupuesto'
                            )

                            mensaje_decision = (
                                'La categoría donde más dinero '
                                'has registrado este mes es '
                                + categoria_nombre
                                + ', con Bs '
                                + format(
                                    categoria_total,
                                    ',.2f'
                                )
                                + '. El presupuesto mensual es '
                                + 'de Bs '
                                + format(
                                    presupuesto.monto,
                                    ',.2f'
                                )
                                + ' y has utilizado aproximadamente '
                                + format(
                                    porcentaje_usado,
                                    '.1f'
                                )
                                + '% del presupuesto. '
                                + 'Quedan Bs '
                                + format(
                                    restante,
                                    ',.2f'
                                )
                                + ' disponibles.'
                            )

                    else:

                        decision = 'amarillo'

                        titulo_decision = (
                            'Análisis de tus gastos'
                        )

                        mensaje_decision = (
                            'La categoría donde más dinero '
                            'has registrado este mes es '
                            + categoria_nombre
                            + ', con Bs '
                            + format(
                                categoria_total,
                                ',.2f'
                            )
                            + '. Actualmente no existe un '
                            + 'presupuesto mensual registrado '
                            + 'para esta categoría, por lo que '
                            + 'no es posible comparar el gasto '
                            + 'con un límite establecido.'
                        )

                else:

                    decision = 'error'

                    titulo_decision = (
                        'No hay suficientes datos'
                    )

                    mensaje_decision = (
                        'Todavía no existen gastos registrados '
                        'este mes para realizar este análisis.'
                    )

            # =================================================
            # CONSULTA: COMPRA O GASTO
            # =================================================

            elif (
                'puedo comprar' in pregunta_minuscula
                or 'puedo comprarme' in pregunta_minuscula
                or 'me alcanza para comprar' in pregunta_minuscula
                or 'me alcanza comprar' in pregunta_minuscula
                or 'puedo gastar' in pregunta_minuscula
                or 'me alcanza para gastar' in pregunta_minuscula
                or 'comprar un' in pregunta_minuscula
                or 'comprar una' in pregunta_minuscula
                or 'vale la pena comprar' in pregunta_minuscula
                or 'es recomendable comprar' in pregunta_minuscula
                or 'puedo adquirir' in pregunta_minuscula
                or 'me alcanza para adquirir' in pregunta_minuscula
            ):

                if monto is None:

                    decision = 'error'

                    titulo_decision = (
                        'Falta el precio'
                    )

                    mensaje_decision = (
                        'Para analizar si puedes realizar '
                        'la compra o gasto, indica el monto. '
                        'Por ejemplo: '
                        '¿Me alcanza para comprar un '
                        'celular de Bs 1200?'
                    )

                elif monto <= Decimal('0'):

                    decision = 'error'

                    titulo_decision = (
                        'Monto no válido'
                    )

                    mensaje_decision = (
                        'El monto de la compra o gasto '
                        'debe ser mayor que cero.'
                    )

                else:

                    dinero_despues = (
                        dinero_disponible
                        - monto
                    )

                    # -----------------------------------------
                    # DETECTAR CATEGORÍA
                    # -----------------------------------------

                    categoria = detectar_categoria(
                        pregunta,
                        request.user
                    )

                    presupuesto = None

                    gastado_categoria = (
                        Decimal('0.00')
                    )

                    restante_presupuesto = None

                    if categoria:

                        fecha_actual = (
                            timezone.localdate()
                        )

                        presupuesto = (
                            Presupuesto.objects
                            .filter(
                                usuario=request.user,
                                categoria=categoria,
                                mes=fecha_actual.month,
                                anio=fecha_actual.year
                            )
                            .first()
                        )

                        if presupuesto:

                            gastado_categoria = (
                                Gasto.objects
                                .filter(
                                    usuario=request.user,
                                    categoria=categoria,
                                    fecha__month=fecha_actual.month,
                                    fecha__year=fecha_actual.year
                                )
                                .aggregate(
                                    total=Sum('monto')
                                )['total']
                                or Decimal('0.00')
                            )

                            restante_presupuesto = (
                                presupuesto.monto
                                - gastado_categoria
                            )

                    # -----------------------------------------
                    # NO ALCANZA EL DINERO
                    # -----------------------------------------

                    if dinero_despues < Decimal('0'):

                        decision = 'rojo'

                        titulo_decision = (
                            'Compra no recomendada'
                        )

                        mensaje_decision = (
                            'Actualmente tienes Bs '
                            + format(
                                dinero_disponible,
                                ',.2f'
                            )
                            + ' disponibles. '
                            + 'La compra o gasto de Bs '
                            + format(
                                monto,
                                ',.2f'
                            )
                            + ' supera tu dinero disponible. '
                            + 'Si realizas la operación, tu saldo '
                            + 'quedaría en Bs '
                            + format(
                                dinero_despues,
                                ',.2f'
                            )
                            + '. No se recomienda realizar '
                            + 'esta operación en las condiciones '
                            + 'actuales.'
                        )

                    else:

                        # -------------------------------------
                        # PORCENTAJE DEL DINERO DISPONIBLE
                        # -------------------------------------

                        if dinero_disponible > Decimal('0'):

                            porcentaje = (
                                monto
                                / dinero_disponible
                            ) * Decimal('100')

                        else:

                            porcentaje = Decimal('100')

                        # -------------------------------------
                        # DECISIÓN BASE
                        # -------------------------------------

                        if porcentaje <= Decimal('20'):

                            decision = 'verde'

                            titulo_decision = (
                                'Compra recomendada'
                            )

                            mensaje_decision = (
                                'Actualmente tienes Bs '
                                + format(
                                    dinero_disponible,
                                    ',.2f'
                                )
                                + ' disponibles. '
                                + 'Después de realizar una '
                                + 'compra o gasto de Bs '
                                + format(
                                    monto,
                                    ',.2f'
                                )
                                + ', tendrías Bs '
                                + format(
                                    dinero_despues,
                                    ',.2f'
                                )
                                + '. La operación representa '
                                + 'aproximadamente '
                                + format(
                                    porcentaje,
                                    '.1f'
                                )
                                + '% del dinero disponible.'
                            )

                        elif porcentaje <= Decimal('50'):

                            decision = 'amarillo'

                            titulo_decision = (
                                'Compra con precaución'
                            )

                            mensaje_decision = (
                                'Actualmente tienes Bs '
                                + format(
                                    dinero_disponible,
                                    ',.2f'
                                )
                                + ' disponibles. '
                                + 'Después de la compra de Bs '
                                + format(
                                    monto,
                                    ',.2f'
                                )
                                + ', tendrías Bs '
                                + format(
                                    dinero_despues,
                                    ',.2f'
                                )
                                + '. La compra representa '
                                + 'aproximadamente '
                                + format(
                                    porcentaje,
                                    '.1f'
                                )
                                + '% del dinero disponible. '
                                + 'Se recomienda revisar los '
                                + 'gastos que todavía debes '
                                + 'realizar.'
                            )

                        else:

                            decision = 'rojo'

                            titulo_decision = (
                                'Compra no recomendada'
                            )

                            mensaje_decision = (
                                'Actualmente tienes Bs '
                                + format(
                                    dinero_disponible,
                                    ',.2f'
                                )
                                + ' disponibles. '
                                + 'La compra de Bs '
                                + format(
                                    monto,
                                    ',.2f'
                                )
                                + ' utilizaría aproximadamente '
                                + format(
                                    porcentaje,
                                    '.1f'
                                )
                                + '% del dinero disponible. '
                                + 'Se recomienda conservar '
                                + 'un mayor margen financiero.'
                            )

                        # -------------------------------------
                        # ANALIZAR PRESUPUESTO
                        # -------------------------------------

                        if presupuesto:

                            presupuesto_despues = (
                                restante_presupuesto
                                - monto
                            )

                            if presupuesto_despues < Decimal('0'):

                                decision = 'rojo'

                                titulo_decision = (
                                    'Compra no recomendada'
                                )

                                mensaje_decision = (
                                    mensaje_decision
                                    + ' Además, para la categoría '
                                    + categoria.nombre
                                    + ', tienes un presupuesto de Bs '
                                    + format(
                                        presupuesto.monto,
                                        ',.2f'
                                    )
                                    + ' para este mes. Ya has utilizado '
                                    + 'Bs '
                                    + format(
                                        gastado_categoria,
                                        ',.2f'
                                    )
                                    + ' y actualmente quedan Bs '
                                    + format(
                                        restante_presupuesto,
                                        ',.2f'
                                    )
                                    + ' disponibles dentro de ese '
                                    + 'presupuesto. Con esta compra '
                                    + 'superarías el presupuesto de '
                                    + 'esta categoría en Bs '
                                    + format(
                                        abs(
                                            presupuesto_despues
                                        ),
                                        ',.2f'
                                    )
                                    + '.'
                                )

                            elif (
                                presupuesto.monto > Decimal('0')
                                and presupuesto_despues
                                <= (
                                    presupuesto.monto
                                    * Decimal('0.20')
                                )
                                and decision == 'verde'
                            ):

                                decision = 'amarillo'

                                titulo_decision = (
                                    'Compra con precaución'
                                )

                                mensaje_decision = (
                                    mensaje_decision
                                    + ' Además, para la categoría '
                                    + categoria.nombre
                                    + ', tienes un presupuesto de Bs '
                                    + format(
                                        presupuesto.monto,
                                        ',.2f'
                                    )
                                    + ' para este mes. Ya has utilizado '
                                    + 'Bs '
                                    + format(
                                        gastado_categoria,
                                        ',.2f'
                                    )
                                    + ' y después de esta compra '
                                    + 'quedarían Bs '
                                    + format(
                                        presupuesto_despues,
                                        ',.2f'
                                    )
                                    + ' disponibles dentro del '
                                    + 'presupuesto de esta categoría.'
                                )

                            else:

                                mensaje_decision = (
                                    mensaje_decision
                                    + ' Además, para la categoría '
                                    + categoria.nombre
                                    + ', tienes un presupuesto de Bs '
                                    + format(
                                        presupuesto.monto,
                                        ',.2f'
                                    )
                                    + ' para este mes. Ya has utilizado '
                                    + 'Bs '
                                    + format(
                                        gastado_categoria,
                                        ',.2f'
                                    )
                                    + ' y actualmente quedan Bs '
                                    + format(
                                        restante_presupuesto,
                                        ',.2f'
                                    )
                                    + ' disponibles dentro de ese '
                                    + 'presupuesto. Después de la '
                                    + 'compra quedarían Bs '
                                    + format(
                                        presupuesto_despues,
                                        ',.2f'
                                    )
                                    + ' disponibles dentro del '
                                    + 'presupuesto de esta categoría.'
                                )

                        elif categoria:

                            mensaje_decision = (
                                mensaje_decision
                                + ' Se identificó la categoría '
                                + categoria.nombre
                                + ', pero no existe un presupuesto '
                                + 'registrado para esta categoría '
                                + 'en el mes actual.'
                            )

            # =================================================
            # CONSULTA: AHORRO
            # =================================================

            elif (
                'ahorrar' in pregunta_minuscula
                or 'ahorro' in pregunta_minuscula
                or 'puedo ahorrar' in pregunta_minuscula
                or 'cuánto puedo ahorrar' in pregunta_minuscula
                or 'cuanto puedo ahorrar' in pregunta_minuscula
                or 'cuánto debería ahorrar' in pregunta_minuscula
                or 'cuanto deberia ahorrar' in pregunta_minuscula
            ):

                if dinero_disponible <= Decimal('0'):

                    decision = 'rojo'

                    titulo_decision = (
                        'No hay capacidad de ahorro'
                    )

                    mensaje_decision = (
                        'Actualmente no existe dinero '
                        'disponible para destinar al ahorro. '
                        'Se recomienda revisar primero '
                        'los gastos registrados.'
                    )

                else:

                    ahorro_sugerido = (
                        dinero_disponible
                        * Decimal('0.10')
                    )

                    decision = 'verde'

                    titulo_decision = (
                        'Capacidad de ahorro'
                    )

                    mensaje_decision = (
                        'Actualmente tienes Bs '
                        + format(
                            dinero_disponible,
                            ',.2f'
                        )
                        + ' disponibles. '
                        + 'Como referencia inicial, '
                        + 'podrías considerar destinar '
                        + 'aproximadamente Bs '
                        + format(
                            ahorro_sugerido,
                            ',.2f'
                        )
                        + ' al ahorro, siempre que no '
                        + 'tengas otros gastos pendientes.'
                    )

            # =================================================
            # CONSULTA NO RECONOCIDA
            # =================================================

            else:

                decision = 'error'

                titulo_decision = (
                    'Consulta no reconocida'
                )

                mensaje_decision = (
                    'La consulta todavía no está dentro '
                    'de las preguntas que el sistema puede '
                    'analizar. Puedes preguntar, por ejemplo: '
                    '¿Cuánto me queda?, '
                    '¿Cuál es mi saldo?, '
                    '¿Me alcanza para comprar un celular '
                    'de Bs 1200?, '
                    '¿Dónde gasto más? '
                    'o ¿Cuánto puedo ahorrar?'
                )

    # ========================================================
    # CONTEXTO
    # ========================================================

    contexto = {
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_gastos_pendientes': total_gastos_pendientes,
        'dinero_disponible': dinero_disponible,
        'pregunta': pregunta,
        'decision': decision,
        'titulo_decision': titulo_decision,
        'mensaje_decision': mensaje_decision,
    }

    return render(
        request,
        'decisiones/consultar.html',
        contexto
    )