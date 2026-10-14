from django.db import models
from django.contrib.auth.models import User


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


class ComercioConfig(models.Model):
    """Configuración de los datos del comercio."""
    razon_social = models.CharField("Razón Social", max_length=150, default="Juguetería S.A.")
    sucursal = models.CharField("Sucursal", max_length=100, default="Casa Central")
    domicilio = models.CharField("Domicilio", max_length=200, default="Av. Corrientes 1234, CABA")

    class Meta:
        verbose_name = "Configuración del Comercio"
        verbose_name_plural = "Configuración del Comercio"

    def __str__(self):
        return f"{self.razon_social} - {self.sucursal}"

    def save(self, *args, **kwargs):
        # Asegurar que siempre exista un solo registro (Singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Caja(models.Model):
    """Cajas disponibles para la venta."""
    nombre = models.CharField("Nombre / Número de Caja", max_length=50, unique=True)
    cajero = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'groups__name': 'Cajero'},
        verbose_name="Cajero Asignado",
        related_name="cajas_asignadas"
    )
    horario_apertura = models.TimeField("Horario de Apertura", default="09:00:00")
    horario_cierre = models.TimeField("Horario de Cierre", default="18:00:00")
    activa = models.BooleanField("Caja Activa", default=True)

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ["nombre"]

    def __str__(self):
        cajero_str = f" - Cajero: {self.cajero.username}" if self.cajero else " - Sin cajero"
        return f"{self.nombre}{cajero_str}"

