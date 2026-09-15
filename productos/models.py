from django.db import models


class Producto(models.Model):
    """
    Coincide con la entidad PRODUCTOS del DER / diagrama de clases del
    proyecto (id, nombre, precio, stock), con el agregado del campo
    codigo_barra necesario para la carga por escaneo desde el celular.
    """
    nombre = models.CharField("Nombre del producto", max_length=100)
    precio = models.DecimalField("Precio", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("Stock", default=0)
    codigo_barra = models.CharField(
        "Código de barras", max_length=50, unique=True, blank=True, null=True
    )
    fecha_alta = models.DateTimeField("Fecha de alta", auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-fecha_alta"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_barra or 'sin código'})"

    @property
    def estado_stock(self):
        if self.stock <= 0:
            return "SIN STOCK"
        if self.stock <= 5:
            return "BAJO"
        return "OK"
