from django.db import migrations
from django.contrib.auth.hashers import make_password


def preparar_cuenta_revision(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    PerfilUsuario = apps.get_model('usuarios', 'PerfilUsuario')

    correo = 'carlosrojas@gmail.com'
    usuario, creado = User.objects.get_or_create(
        username=correo,
        defaults={
            'email': correo,
            'is_active': True,
        },
    )

    usuario.email = correo
    usuario.is_active = True
    usuario.password = make_password('Carlos2026!Prueba')
    usuario.save(update_fields=['email', 'is_active', 'password'])

    PerfilUsuario.objects.get_or_create(
        usuario=usuario,
        defaults={'nombre_completo': 'Carlos Rojas'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(preparar_cuenta_revision, migrations.RunPython.noop),
    ]
