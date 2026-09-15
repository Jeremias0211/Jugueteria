from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProductoForm
from .models import Producto


def carga_productos(request):
    """Caso de uso: Registrar Ingreso de Mercadería / Registrar Nuevo (Depósito)."""
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f"Producto «{producto.nombre}» cargado correctamente.")
            return redirect("carga_productos")
        else:
            messages.error(request, "Revisá los datos del formulario: hay errores.")
    else:
        form = ProductoForm()

    query = request.GET.get("q", "").strip()
    productos = Producto.objects.all()
    if query:
        productos = productos.filter(nombre__icontains=query)

    return render(request, "productos/carga.html", {
        "form": form,
        "productos": productos,
        "query": query,
        "total_productos": Producto.objects.count(),
    })


def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto «{nombre}» eliminado.")
    return redirect("carga_productos")
