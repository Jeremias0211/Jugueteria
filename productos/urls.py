from django.urls import path

from . import views


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

]
