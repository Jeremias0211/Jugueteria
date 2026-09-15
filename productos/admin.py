from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_barra", "precio", "stock", "estado_stock", "fecha_alta")
    search_fields = ("nombre", "codigo_barra")
    list_filter = ("fecha_alta",)
