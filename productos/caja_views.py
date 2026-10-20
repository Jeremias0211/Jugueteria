from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Caja, SesionCaja, Producto, Venta, DetalleVenta, Voucher, NotaCredito, Achique
from .forms import AperturaCajaForm, AchiqueForm, VoucherForm, CierreCajaForm


@login_required
def caja_dashboard(request):
    user = request.user
    if user.is_superuser or user.groups.filter(name__in=["Administrador", "Gerente"]).exists():
        cajas = Caja.objects.all()
        caja_id = request.GET.get('caja_id')
        if caja_id:
            caja = get_object_or_404(Caja, pk=caja_id)
        else:
            caja = cajas.first()
    else:
        caja = Caja.objects.filter(cajero=user).first()
        cajas = [caja] if caja else []

    if not caja:
        messages.error(request, "No tiene ninguna caja asignada. Contacte al Administrador.")
        return redirect("carga_productos")

    sesion_activa = SesionCaja.objects.filter(caja=caja, cerrada=False).first()

    if not sesion_activa:
        if request.method == "POST":
            form = AperturaCajaForm(request.POST)
            if form.is_valid():
                sesion = form.save(commit=False)
                sesion.caja = caja
                sesion.cajero = user
                sesion.estado = 'VENTAS'
                sesion.save()
                messages.success(request, f"Caja {caja.nombre} abierta correctamente con monto inicial ${sesion.monto_inicial}.")
                return redirect("caja_dashboard")
        else:
            form = AperturaCajaForm()
        return render(request, "productos/caja_apertura.html", {"form": form, "caja": caja, "cajas": cajas})

    cart_key = f"caja_cart_{sesion_activa.pk}"
    if cart_key not in request.session:
        request.session[cart_key] = {}

    cart = request.session[cart_key]
    cart_items = []
    cart_total = Decimal('0.00')
    for p_id_str, qty in cart.items():
        try:
            producto = Producto.objects.get(pk=int(p_id_str))
            subtotal = producto.precio * qty
            cart_total += subtotal
            cart_items.append({
                "producto": producto,
                "cantidad": qty,
                "subtotal": subtotal,
                "id_str": p_id_str
            })
        except Producto.DoesNotExist:
            pass

    productos_disponibles = Producto.objects.filter(stock__gt=0)
    totales = sesion_activa.calcular_totales()
    ventas_recientes = sesion_activa.ventas.all()[:15]
    achiques = sesion_activa.achiques.all()
    vouchers_disponibles = Voucher.objects.filter(consumido=False)

    return render(request, "productos/caja_punto_venta.html", {
        "sesion": sesion_activa,
        "caja": caja,
        "cajas": cajas,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "productos": productos_disponibles,
        "totales": totales,
        "ventas_recientes": ventas_recientes,
        "achiques": achiques,
        "vouchers_disponibles": vouchers_disponibles,
    })


@login_required
def caja_agregar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    sesion = SesionCaja.objects.filter(cajero=request.user, cerrada=False).first()
    if not sesion and request.user.is_superuser:
        sesion = SesionCaja.objects.filter(cerrada=False).first()
    
    if not sesion:
        messages.error(request, "No hay una sesión de caja abierta.")
        return redirect("caja_dashboard")

    cart_key = f"caja_cart_{sesion.pk}"
    cart = request.session.get(cart_key, {})

    p_id_str = str(producto_id)
    cantidad_solicitada = int(request.POST.get("cantidad", 1))

    current_qty = cart.get(p_id_str, 0)
    nueva_qty = current_qty + cantidad_solicitada

    if nueva_qty > producto.stock:
        messages.error(request, f"Stock insuficiente para «{producto.nombre}». Stock disponible: {producto.stock}")
    else:
        cart[p_id_str] = nueva_qty
        request.session[cart_key] = cart
        messages.success(request, f"Agregado {producto.nombre} al carrito.")

    return redirect("caja_dashboard")


@login_required
def caja_quitar_carrito(request, producto_id):
    sesion = SesionCaja.objects.filter(cajero=request.user, cerrada=False).first()
    if not sesion and request.user.is_superuser:
        sesion = SesionCaja.objects.filter(cerrada=False).first()
    if sesion:
        cart_key = f"caja_cart_{sesion.pk}"
        cart = request.session.get(cart_key, {})
        p_id_str = str(producto_id)
        if p_id_str in cart:
            del cart[p_id_str]
            request.session[cart_key] = cart
    return redirect("caja_dashboard")


@login_required
def caja_procesar_venta(request):
    sesion = SesionCaja.objects.filter(cajero=request.user, cerrada=False).first()
    if not sesion and request.user.is_superuser:
        sesion = SesionCaja.objects.filter(cerrada=False).first()

    if not sesion:
        messages.error(request, "No hay sesión de caja abierta.")
        return redirect("caja_dashboard")

    cart_key = f"caja_cart_{sesion.pk}"
    cart = request.session.get(cart_key, {})
    if not cart:
        messages.error(request, "El carrito está vacío.")
        return redirect("caja_dashboard")

    items = []
    total_venta = Decimal('0.00')
    for p_id_str, qty in cart.items():
        producto = get_object_or_404(Producto, pk=int(p_id_str))
        subtotal = producto.precio * qty
        total_venta += subtotal
        items.append((producto, qty, subtotal))

    metodo_pago = request.POST.get("metodo_pago", "EFECTIVO")
    monto_efectivo_pagado = Decimal(request.POST.get("monto_efectivo_pagado", "0") or "0")
    voucher_codigo = request.POST.get("voucher_codigo", "").strip()

    monto_ef = Decimal('0.00')
    monto_dig = Decimal('0.00')
    monto_vou = Decimal('0.00')
    vuelto = Decimal('0.00')
    voucher_obj = None

    if metodo_pago == "EFECTIVO":
        if monto_efectivo_pagado < total_venta:
            messages.error(request, f"El monto en efectivo entregado (${monto_efectivo_pagado}) es menor al total de la venta (${total_venta}).")
            return redirect("caja_dashboard")
        monto_ef = total_venta
        vuelto = monto_efectivo_pagado - total_venta

    elif metodo_pago == "DIGITAL":
        monto_dig = total_venta

    elif metodo_pago == "VOUCHER":
        if not voucher_codigo:
            messages.error(request, "Debe ingresar el código de referencia del voucher.")
            return redirect("caja_dashboard")
        voucher_obj = Voucher.objects.filter(codigo_referencia=voucher_codigo, consumido=False).first()
        if not voucher_obj:
            messages.error(request, "Voucher inválido o ya consumido.")
            return redirect("caja_dashboard")
        
        val_voucher = voucher_obj.monto_precargado
        if total_venta <= val_voucher:
            monto_vou = total_venta
        else:
            monto_vou = val_voucher
            restante = total_venta - val_voucher
            dif_metodo = request.POST.get("metodo_diferencia", "EFECTIVO")
            if dif_metodo == "EFECTIVO":
                monto_ef = restante
                monto_ef_pagado_dif = Decimal(request.POST.get("monto_efectivo_pagado", "0") or "0")
                if monto_ef_pagado_dif < restante:
                    messages.error(request, f"Faltan fondos en efectivo para cubrir la diferencia (${restante}).")
                    return redirect("caja_dashboard")
                vuelto = monto_ef_pagado_dif - restante
            else:
                monto_dig = restante

    elif metodo_pago == "MIXTO_EFECTIVO_DIGITAL":
        monto_ef = Decimal(request.POST.get("monto_efectivo", "0") or "0")
        monto_dig = Decimal(request.POST.get("monto_digital", "0") or "0")
        if (monto_ef + monto_dig) < total_venta:
            messages.error(request, "La suma de efectivo y digital no cubre el total de la venta.")
            return redirect("caja_dashboard")
        vuelto = max(Decimal('0.00'), monto_ef - (total_venta - monto_dig))
        monto_ef = min(monto_ef, total_venta)

    venta = Venta.objects.create(
        sesion_caja=sesion,
        cajero=request.user,
        total=total_venta,
        monto_efectivo=monto_ef,
        monto_digital=monto_dig,
        monto_voucher=monto_vou,
        voucher_utilizado=voucher_obj,
        vuelto=vuelto,
    )

    for producto, qty, subtotal in items:
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=qty,
            precio_unitario=producto.precio,
            subtotal=subtotal
        )
        producto.stock -= qty
        producto.save()

    if voucher_obj:
        voucher_obj.consumido = True
        voucher_obj.save()

    request.session[cart_key] = {}
    messages.success(request, f"Venta #{venta.pk} realizada con éxito. Total: ${total_venta} (Vuelto: ${vuelto})")
    return redirect("caja_dashboard")


@login_required
def caja_achique(request):
    sesion = SesionCaja.objects.filter(cajero=request.user, cerrada=False).first()
    if not sesion and request.user.is_superuser:
        sesion = SesionCaja.objects.filter(cerrada=False).first()

    if not sesion:
        messages.error(request, "No hay sesión de caja abierta.")
        return redirect("caja_dashboard")

    if request.method == "POST":
        form = AchiqueForm(request.POST)
        if form.is_valid():
            achique = form.save(commit=False)
            achique.sesion_caja = sesion
            achique.usuario = request.user
            achique.save()
            messages.success(request, f"Achique registrado por ${achique.monto}.")
            return redirect("caja_dashboard")
    else:
        form = AchiqueForm()

    return render(request, "productos/caja_achique.html", {"form": form, "sesion": sesion})


@login_required
def caja_vouchers(request):
    vouchers = Voucher.objects.all()
    if request.method == "POST":
        form = VoucherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Voucher / Tarjeta de regalo creada exitosamente.")
            return redirect("caja_vouchers")
    else:
        form = VoucherForm()

    return render(request, "productos/caja_vouchers.html", {"form": form, "vouchers": vouchers})


@login_required
def caja_anular_venta(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    if venta.anulada:
        messages.error(request, "La venta ya está anulada.")
        return redirect("caja_dashboard")

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        if not motivo:
            messages.error(request, "Debe indicar el motivo de la anulación para generar la Nota de Crédito.")
            return redirect("caja_dashboard")

        NotaCredito.objects.create(
            venta=venta,
            motivo=motivo,
            usuario=request.user
        )
        venta.anulada = True
        venta.save()

        for detalle in venta.detalles.all():
            prod = detalle.producto
            prod.stock += detalle.cantidad
            prod.save()

        if venta.voucher_utilizado:
            v = venta.voucher_utilizado
            v.consumido = False
            v.save()

        messages.success(request, f"Venta #{venta.pk} anulada mediante Nota de Crédito.")
        return redirect("caja_dashboard")

    return render(request, "productos/caja_anular_venta.html", {"venta": venta})


@login_required
def caja_cierre(request):
    sesion = SesionCaja.objects.filter(cajero=request.user, cerrada=False).first()
    if not sesion and request.user.is_superuser:
        sesion = SesionCaja.objects.filter(cerrada=False).first()

    if not sesion:
        messages.error(request, "No hay sesión de caja abierta.")
        return redirect("caja_dashboard")

    totales = sesion.calcular_totales()

    if request.method == "POST":
        form = CierreCajaForm(request.POST, instance=sesion)
        if form.is_valid():
            sesion = form.save(commit=False)
            monto_declarado = sesion.monto_declarado_fisico
            monto_esperado = Decimal(str(totales["monto_esperado"]))
            diferencia = monto_declarado - monto_esperado

            sesion.diferencia = diferencia
            sesion.cerrada = True
            sesion.estado = 'CERRADA'
            sesion.fecha_cierre = timezone.now()
            sesion.save()

            if abs(diferencia) > Decimal('3000.00'):
                messages.warning(request, f"Caja cerrada con una diferencia de ${diferencia}, la cual supera el límite permitido de $3000.")
            else:
                messages.success(request, f"Caja cerrada exitosamente. Diferencia: ${diferencia}.")

            return redirect("caja_reporte", sesion_id=sesion.pk)
    else:
        form = CierreCajaForm(instance=sesion)

    return render(request, "productos/caja_cierre.html", {
        "form": form,
        "sesion": sesion,
        "totales": totales,
    })


@login_required
def caja_reporte(request, sesion_id):
    sesion = get_object_or_404(SesionCaja, pk=sesion_id)
    totales = sesion.calcular_totales()
    return render(request, "productos/caja_reporte.html", {
        "sesion": sesion,
        "totales": totales,
    })
