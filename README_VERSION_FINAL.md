# Finanzas Personales - versión de revisión para cliente

Esta carpeta contiene la versión local de revisión del sistema **Finanzas Personales**.
Está preparada para que una persona con Windows pueda abrir el sistema desde el Explorador de archivos sin entrar manualmente a `templates` ni abrir archivos HTML directamente.

## Cómo abrirlo

1. Descomprimir toda la carpeta.
2. Hacer doble clic en:

   **ABRIR_FINANZAS.vbs**

3. Esperar unos segundos. El sistema iniciará Django en segundo plano y abrirá automáticamente el navegador en:

   `http://127.0.0.1:8000/`

4. Iniciar sesión con la cuenta de revisión:

   **Correo:** `carlosrojas@gmail.com`

   **Contraseña:** `Carlos2026!Prueba`

## Cómo cerrar el sistema

Hacer doble clic en:

**CERRAR_FINANZAS.vbs**

## Requisito del equipo de revisión

Esta versión local requiere **Python 3.14** instalado en Windows. Si Django todavía no está instalado, el archivo `ABRIR_FINANZAS.vbs` intenta instalar automáticamente la versión indicada en `requirements.txt`.

Todas las dependencias de Python y Django necesarias para la revisión están incluidas dentro del paquete. No necesita conexión a Internet para instalar componentes. El sistema funciona localmente con SQLite y no necesita publicar nada en Internet.

## Importante

No abrir directamente estos archivos desde el Explorador:

- `templates/base.html`
- `templates/usuarios/inicio.html`
- cualquier otro `.html` dentro de `templates`

Esos archivos son plantillas Django y deben ser procesados por el servidor.

## Módulos incluidos

- Registro e inicio de sesión.
- Recuperación y cambio de contraseña.
- Dashboard financiero.
- Ingresos.
- Gastos.
- Gastos pendientes.
- Presupuesto.
- Metas de ahorro.
- Historial.
- Decisiones financieras.
- Administración Django.

## Datos y migraciones

La base de datos incluida conserva los datos de revisión existentes. Las migraciones también crean las categorías generales si se instala el proyecto sobre una base nueva.
