from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProductoForm, ComercioConfigForm, CajaForm, UsuarioForm
from .models import Producto, ComercioConfig, Caja


def es_administrador_o_gerente(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.groups.filter(name__in=["Administrador", "Gerente"]).exists())


def es_personal_autorizado(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.groups.filter(name__in=["Administrador", "Gerente", "Deposito", "Cajero"]).exists())


def asegurar_grupos():
    """Asegura que existan los grupos de roles requeridos."""
    roles = ["Administrador", "Gerente", "Deposito", "Cajero"]
    for rol in roles:
        Group.objects.get_or_create(name=rol)


@user_passes_test(es_personal_autorizado)
def carga_productos(request):
    """Pantalla principal de carga y gestión de productos."""

    if request.method == "POST":
        form = ProductoForm(request.POST)

        if form.is_valid():
            producto = form.save()

            messages.success(
                request,
                f"Producto «{producto.nombre}» cargado correctamente."
            )

            return redirect("carga_productos")

        else:
            messages.error(
                request,
                "Revisá los datos del formulario: hay errores."
            )

    else:
        form = ProductoForm()

    query = request.GET.get("q", "").strip()

    productos = Producto.objects.all()

    if query:
        productos = productos.filter(nombre__icontains=query)

    return render(
        request,
        "productos/carga.html",
        {
            "form": form,
            "productos": productos,
            "query": query,
            "total_productos": Producto.objects.count(),
        }
    )


@user_passes_test(es_personal_autorizado)
def buscar_por_codigo(request):
    """
    Busca un producto utilizando su código de barras.
    Se utiliza desde JavaScript cuando la cámara detecta un código.
    """

    codigo = request.GET.get("codigo", "").strip()

    if not codigo:
        return JsonResponse({
            "encontrado": False,
            "error": "No se recibió ningún código."
        })

    producto = Producto.objects.filter(
        codigo_barra=codigo
    ).first()

    if producto:

        return JsonResponse({
            "encontrado": True,
            "id": producto.id,
            "nombre": producto.nombre,
            "precio": str(producto.precio),
            "stock": producto.stock,
            "codigo_barra": producto.codigo_barra,
        })

    return JsonResponse({
        "encontrado": False,
        "codigo_barra": codigo,
    })


@user_passes_test(es_personal_autorizado)
def agregar_stock(request, pk):
    """
    Agrega unidades al stock de un producto existente.
    """

    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":

        try:
            cantidad = int(request.POST.get("cantidad", 0))
        except (ValueError, TypeError):
            cantidad = 0

        if cantidad > 0:

            producto.stock += cantidad
            producto.save()

            messages.success(
                request,
                f"Se agregaron {cantidad} unidades a «{producto.nombre}»."
            )

        else:

            messages.error(
                request,
                "La cantidad debe ser mayor a 0."
            )

    return redirect("carga_productos")


@user_passes_test(es_personal_autorizado)
def eliminar_producto(request, pk):

    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":

        nombre = producto.nombre

        producto.delete()

        messages.success(
            request,
            f"Producto «{nombre}» eliminado."
        )

    return redirect("carga_productos")


# --- PANEL DE ADMINISTRACIÓN ---

@user_passes_test(es_administrador_o_gerente)
def admin_dashboard(request):
    """Panel principal del Administrador del Sistema."""
    asegurar_grupos()
    comercio = ComercioConfig.load()
    usuarios = User.objects.all().prefetch_related("groups")
    cajas = Caja.objects.all().select_related("cajero")

    return render(
        request,
        "productos/admin_dashboard.html",
        {
            "comercio": comercio,
            "usuarios": usuarios,
            "cajas": cajas,
            "total_usuarios": usuarios.count(),
            "total_cajas": cajas.count(),
        }
    )


@user_passes_test(es_administrador_o_gerente)
def admin_comercio(request):
    """Configurar datos del comercio (sucursal, domicilio, razón social)."""
    comercio = ComercioConfig.load()

    if request.method == "POST":
        form = ComercioConfigForm(request.POST, instance=comercio)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos del comercio actualizados exitosamente.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Error al actualizar los datos del comercio.")
    else:
        form = ComercioConfigForm(instance=comercio)

    return render(request, "productos/admin_comercio.html", {"form": form, "comercio": comercio})


@user_passes_test(es_administrador_o_gerente)
def admin_usuario_crear(request):
    """Crear y administrar usuarios y asignar roles (Administrador, Gerente, Deposito, Cajero)."""
    asegurar_grupos()

    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"Usuario «{usuario.username}» creado correctamente.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Error al crear el usuario. Verifique los datos.")
    else:
        form = UsuarioForm()

    return render(request, "productos/admin_usuario_form.html", {"form": form, "accion": "Crear"})


@user_passes_test(es_administrador_o_gerente)
def admin_usuario_editar(request, pk):
    """Editar usuario y su rol."""
    asegurar_grupos()
    usuario = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario «{usuario.username}» actualizado correctamente.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Error al actualizar el usuario.")
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, "productos/admin_usuario_form.html", {"form": form, "accion": "Editar", "usuario_obj": usuario})


@user_passes_test(es_administrador_o_gerente)
def admin_usuario_eliminar(request, pk):
    """Eliminar usuario."""
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        nombre = usuario.username
        if usuario.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            messages.error(request, "No se puede eliminar al único administrador principal del sistema.")
        else:
            usuario.delete()
            messages.success(request, f"Usuario «{nombre}» eliminado correctamente.")
    return redirect("admin_dashboard")


@user_passes_test(es_administrador_o_gerente)
def admin_caja_crear(request):
    """Crear caja, configurar horarios de apertura y cierre y asignar cajero."""
    asegurar_grupos()

    if request.method == "POST":
        form = CajaForm(request.POST)
        if form.is_valid():
            caja = form.save()
            messages.success(request, f"Caja «{caja.nombre}» creada correctamente.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Error al crear la caja. Verifique los datos.")
    else:
        form = CajaForm()

    return render(request, "productos/admin_caja_form.html", {"form": form, "accion": "Crear"})


@user_passes_test(es_administrador_o_gerente)
def admin_caja_editar(request, pk):
    """Editar caja, horarios y cajero asignado."""
    asegurar_grupos()
    caja = get_object_or_404(Caja, pk=pk)

    if request.method == "POST":
        form = CajaForm(request.POST, instance=caja)
        if form.is_valid():
            form.save()
            messages.success(request, f"Caja «{caja.nombre}» actualizada correctamente.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Error al actualizar la caja.")
    else:
        form = CajaForm(instance=caja)

    return render(request, "productos/admin_caja_form.html", {"form": form, "accion": "Editar", "caja_obj": caja})


@user_passes_test(es_administrador_o_gerente)
def admin_caja_eliminar(request, pk):
    """Eliminar caja."""
    caja = get_object_or_404(Caja, pk=pk)
    if request.method == "POST":
        nombre = caja.nombre
        caja.delete()
        messages.success(request, f"Caja «{nombre}» eliminada correctamente.")
    return redirect("admin_dashboard")
