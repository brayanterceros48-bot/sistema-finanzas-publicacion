from django.db import migrations


CATEGORIAS_INICIALES = [
    'Alimentación',
    'Vivienda',
    'Transporte',
    'Servicios',
    'Salud',
    'Educación',
    'Entretenimiento',
    'Compras',
    'Deudas',
    'Otros',
]


def crear_categorias(apps, schema_editor):
    Categoria = apps.get_model('finanzas', 'Categoria')
    for nombre in CATEGORIAS_INICIALES:
        Categoria.objects.get_or_create(nombre=nombre, usuario=None)


def eliminar_categorias(apps, schema_editor):
    Categoria = apps.get_model('finanzas', 'Categoria')
    Categoria.objects.filter(
        usuario=None,
        nombre__in=CATEGORIAS_INICIALES,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0003_metaahorro'),
    ]

    operations = [
        migrations.RunPython(crear_categorias, eliminar_categorias),
    ]
