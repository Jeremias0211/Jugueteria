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


class SesionCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name="sesiones")
    cajero = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sesiones_caja")
    estado = models.CharField(
        max_length=20,
        choices=[('APERTURA', 'Apertura'), ('VENTAS', 'Ventas'), ('CERRADA', 'Cerrada')],
        default='APERTURA'
    )
    monto_inicial = models.DecimalField("Monto Inicial en Efectivo", max_digits=10, decimal_places=2, default=0)
    fecha_apertura = models.DateTimeField("Fecha y Hora de Apertura", auto_now_add=True)
    fecha_cierre = models.DateTimeField("Fecha y Hora de Cierre", null=True, blank=True)
    monto_declarado_fisico = models.DecimalField("Monto Físico Declarado", max_digits=10, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField("Diferencia", max_digits=10, decimal_places=2, null=True, blank=True)
    cerrada = models.BooleanField("Caja Cerrada", default=False)

    class Meta:
        verbose_name = "Sesión de Caja"
        verbose_name_plural = "Sesiones de Caja"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return f"Sesión {self.pk} - {self.caja.nombre} ({self.cajero.username}) - {self.estado}"

    def calcular_totales(self):
        ventas_activas = self.ventas.filter(anulada=False)
        total_efectivo = sum(v.monto_efectivo for v in ventas_activas)
        total_digital = sum(v.monto_digital for v in ventas_activas)
        total_voucher = sum(v.monto_voucher for v in ventas_activas)
        total_achiques = sum(a.monto for a in self.achiques.all())
        monto_esperado = float(self.monto_inicial) + float(total_efectivo) - float(total_achiques)
        return {
            "total_efectivo": total_efectivo,
            "total_digital": total_digital,
            "total_voucher": total_voucher,
            "total_achiques": total_achiques,
            "monto_esperado": monto_esperado,
        }


class Voucher(models.Model):
    codigo_referencia = models.CharField("Número de Referencia", max_length=50, unique=True)
    monto_precargado = models.DecimalField("Monto Precargado", max_digits=10, decimal_places=2)
    consumido = models.BooleanField("Consumido", default=False)
    metodo_pago_carga = models.CharField(
        "Método de Pago de Carga",
        max_length=20,
        choices=[('EFECTIVO', 'Efectivo'), ('DIGITAL', 'Digital')],
        default='EFECTIVO'
    )
    fecha_creacion = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    class Meta:
        verbose_name = "Voucher / Tarjeta de Regalo"
        verbose_name_plural = "Vouchers / Tarjetas de Regalo"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        estado_str = "Consumido" if self.consumido else "Disponible"
        return f"Voucher #{self.codigo_referencia} - ${self.monto_precargado} ({estado_str})"


class Venta(models.Model):
    sesion_caja = models.ForeignKey(SesionCaja, on_delete=models.CASCADE, related_name="ventas")
    cajero = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField("Fecha y Hora", auto_now_add=True)
    total = models.DecimalField("Total", max_digits=10, decimal_places=2)
    monto_efectivo = models.DecimalField("Pago en Efectivo", max_digits=10, decimal_places=2, default=0)
    monto_digital = models.DecimalField("Pago Digital", max_digits=10, decimal_places=2, default=0)
    monto_voucher = models.DecimalField("Pago con Voucher", max_digits=10, decimal_places=2, default=0)
    voucher_utilizado = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas")
    vuelto = models.DecimalField("Vuelto", max_digits=10, decimal_places=2, default=0)
    anulada = models.BooleanField("Anulada", default=False)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]

    def __str__(self):
        estado = " [ANULADA]" if self.anulada else ""
        return f"Venta #{self.pk} - ${self.total}{estado}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField("Cantidad")
    precio_unitario = models.DecimalField("Precio Unitario", max_digits=10, decimal_places=2)
    subtotal = models.DecimalField("Subtotal", max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} (${self.subtotal})"


class NotaCredito(models.Model):
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name="nota_credito")
    fecha = models.DateTimeField("Fecha y Hora", auto_now_add=True)
    motivo = models.TextField("Motivo de Anulación")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario que anula")

    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Nota de Crédito NC-{self.pk} (Venta #{self.venta.pk})"


class Achique(models.Model):
    sesion_caja = models.ForeignKey(SesionCaja, on_delete=models.CASCADE, related_name="achiques")
    fecha = models.DateTimeField("Fecha y Hora", auto_now_add=True)
    monto = models.DecimalField("Monto", max_digits=10, decimal_places=2)
    motivo = models.TextField("Motivo del Retiro")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")

    class Meta:
        verbose_name = "Achique"
        verbose_name_plural = "Achiques"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Achique #{self.pk} - ${self.monto} ({self.motivo})"

