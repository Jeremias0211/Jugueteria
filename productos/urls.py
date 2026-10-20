from django.urls import path

from . import views
from . import caja_views


urlpatterns = [

    path(
        "",
        views.carga_productos,
        name="carga_productos"
    ),

    path(
        "buscar-codigo/",
        views.buscar_por_codigo,
        name="buscar_por_codigo"
    ),

    path(
        "agregar-stock/<int:pk>/",
        views.agregar_stock,
        name="agregar_stock"
    ),

    path(
        "eliminar/<int:pk>/",
        views.eliminar_producto,
        name="eliminar_producto"
    ),

    # Panel de Administración
    path(
        "admin-panel/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),
    path(
        "admin-panel/comercio/",
        views.admin_comercio,
        name="admin_comercio"
    ),
    path(
        "admin-panel/usuarios/nuevo/",
        views.admin_usuario_crear,
        name="admin_usuario_crear"
    ),
    path(
        "admin-panel/usuarios/editar/<int:pk>/",
        views.admin_usuario_editar,
        name="admin_usuario_editar"
    ),
    path(
        "admin-panel/usuarios/eliminar/<int:pk>/",
        views.admin_usuario_eliminar,
        name="admin_usuario_eliminar"
    ),
    path(
        "admin-panel/cajas/nueva/",
        views.admin_caja_crear,
        name="admin_caja_crear"
    ),
    path(
        "admin-panel/cajas/editar/<int:pk>/",
        views.admin_caja_editar,
        name="admin_caja_editar"
    ),
    path(
        "admin-panel/cajas/eliminar/<int:pk>/",
        views.admin_caja_eliminar,
        name="admin_caja_eliminar"
    ),

    # Módulo Caja (Punto de Venta)
    path("caja/", caja_views.caja_dashboard, name="caja_dashboard"),
    path("caja/agregar-carrito/<int:producto_id>/", caja_views.caja_agregar_carrito, name="caja_agregar_carrito"),
    path("caja/quitar-carrito/<int:producto_id>/", caja_views.caja_quitar_carrito, name="caja_quitar_carrito"),
    path("caja/procesar-venta/", caja_views.caja_procesar_venta, name="caja_procesar_venta"),
    path("caja/achique/", caja_views.caja_achique, name="caja_achique"),
    path("caja/vouchers/", caja_views.caja_vouchers, name="caja_vouchers"),
    path("caja/anular-venta/<int:venta_id>/", caja_views.caja_anular_venta, name="caja_anular_venta"),
    path("caja/cierre/", caja_views.caja_cierre, name="caja_cierre"),
    path("caja/reporte/<int:sesion_id>/", caja_views.caja_reporte, name="caja_reporte"),

]
