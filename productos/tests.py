from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from decimal import Decimal
from productos.models import Producto, ComercioConfig, Caja, SesionCaja, Venta, Voucher, Achique, NotaCredito


class AdminPanelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear grupos de roles
        self.grupo_admin = Group.objects.create(name='Administrador')
        self.grupo_gerente = Group.objects.create(name='Gerente')
        self.grupo_deposito = Group.objects.create(name='Deposito')
        self.grupo_cajero = Group.objects.create(name='Cajero')

        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='password123'
        )
        self.admin_user.groups.add(self.grupo_admin)

    def test_comercio_config_singleton(self):
        config1 = ComercioConfig.load()
        config1.razon_social = "Juguetería Test S.A."
        config1.save()

        config2 = ComercioConfig.load()
        self.assertEqual(config2.razon_social, "Juguetería Test S.A.")
        self.assertEqual(ComercioConfig.objects.count(), 1)

    def test_crear_caja_y_asignar_cajero(self):
        cajero_user = User.objects.create_user(
            username='cajero1',
            password='password123',
            first_name='Juan',
            last_name='Pérez'
        )
        cajero_user.groups.add(self.grupo_cajero)

        caja = Caja.objects.create(
            nombre="Caja 1",
            cajero=cajero_user,
            horario_apertura="08:00:00",
            horario_cierre="20:00:00",
            activa=True
        )

        self.assertEqual(caja.nombre, "Caja 1")
        self.assertEqual(caja.cajero, cajero_user)
        self.assertTrue(caja.activa)

    def test_admin_dashboard_view(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel del Administrador")

    def test_admin_comercio_view(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get('/admin-panel/comercio/')
        self.assertEqual(response.status_code, 200)

    def test_admin_usuario_crear_view(self):
        self.client.login(username='admin', password='password123')
        response = self.client.post('/admin-panel/usuarios/nuevo/', {
            'username': 'nuevo_gerente',
            'first_name': 'Maria',
            'last_name': 'Gomez',
            'email': 'maria@example.com',
            'password': 'password123',
            'rol': self.grupo_gerente.pk,
            'is_active': True
        })
        self.assertRedirects(response, '/admin-panel/')
        self.assertTrue(User.objects.filter(username='nuevo_gerente').exists())
        nuevo = User.objects.get(username='nuevo_gerente')
        self.assertTrue(nuevo.groups.filter(name='Gerente').exists())

    def test_admin_caja_crear_view(self):
        self.client.login(username='admin', password='password123')
        response = self.client.post('/admin-panel/cajas/nueva/', {
            'nombre': 'Caja 2',
            'horario_apertura': '09:00',
            'horario_cierre': '18:00',
            'activa': True
        })
        self.assertRedirects(response, '/admin-panel/')
        self.assertTrue(Caja.objects.filter(nombre='Caja 2').exists())


class CajaModuleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.grupo_cajero = Group.objects.get_or_create(name='Cajero')[0]
        self.cajero_user = User.objects.create_user(
            username='cajero_test',
            password='password123'
        )
        self.cajero_user.groups.add(self.grupo_cajero)

        self.caja = Caja.objects.create(
            nombre="Caja Test",
            cajero=self.cajero_user,
            activa=True
        )

        self.producto = Producto.objects.create(
            nombre="Lego Test",
            precio=Decimal("1000.00"),
            stock=10,
            codigo_barra="7791234567890"
        )

    def test_caja_apertura_y_ventas_efectivo(self):
        self.client.login(username='cajero_test', password='password123')
        response = self.client.post('/caja/', {'monto_inicial': '5000.00'})
        self.assertRedirects(response, '/caja/')

        sesion = SesionCaja.objects.get(caja=self.caja, cerrada=False)
        self.assertEqual(sesion.monto_inicial, Decimal("5000.00"))

        self.client.post(f'/caja/agregar-carrito/{self.producto.pk}/', {'cantidad': '2'})
        response = self.client.post('/caja/procesar-venta/', {
            'metodo_pago': 'EFECTIVO',
            'monto_efectivo_pagado': '3000.00'
        })
        self.assertRedirects(response, '/caja/')

        venta = Venta.objects.last()
        self.assertEqual(venta.total, Decimal("2000.00"))
        self.assertEqual(venta.monto_efectivo, Decimal("2000.00"))
        self.assertEqual(venta.vuelto, Decimal("1000.00"))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)

    def test_voucher_y_anulacion(self):
        self.client.login(username='cajero_test', password='password123')
        v = Voucher.objects.create(
            codigo_referencia="VOU-999",
            monto_precargado=Decimal("500.00"),
            metodo_pago_carga="EFECTIVO"
        )
        self.client.post('/caja/', {'monto_inicial': '1000.00'})
        sesion = SesionCaja.objects.get(caja=self.caja, cerrada=False)

        p2 = Producto.objects.create(nombre="Auto", precio=Decimal("300.00"), stock=5, codigo_barra="111")
        cart_key = f"caja_cart_{sesion.pk}"
        session = self.client.session
        session[cart_key] = {str(p2.pk): 1}
        session.save()

        response = self.client.post('/caja/procesar-venta/', {
            'metodo_pago': 'VOUCHER',
            'voucher_codigo': 'VOU-999'
        })
        self.assertRedirects(response, '/caja/')
        v.refresh_from_db()
        self.assertTrue(v.consumido)

        venta = Venta.objects.last()
        self.assertEqual(venta.monto_voucher, Decimal("300.00"))

        response = self.client.post(f'/caja/anular-venta/{venta.pk}/', {
            'motivo': 'Error de cobro'
        })
        self.assertRedirects(response, '/caja/')
        venta.refresh_from_db()
        self.assertTrue(venta.anulada)
        self.assertTrue(hasattr(venta, 'nota_credito'))
        v.refresh_from_db()
        self.assertFalse(v.consumido)

    def test_cierre_caja(self):
        self.client.login(username='cajero_test', password='password123')
        self.client.post('/caja/', {'monto_inicial': '2000.00'})
        sesion = SesionCaja.objects.get(caja=self.caja, cerrada=False)

        Achique.objects.create(
            sesion_caja=sesion,
            monto=Decimal("500.00"),
            motivo="Pago flete",
            usuario=self.cajero_user
        )

        response = self.client.post('/caja/cierre/', {
            'monto_declarado_fisico': '1500.00'
        })
        sesion.refresh_from_db()
        self.assertTrue(sesion.cerrada)
        self.assertEqual(sesion.diferencia, Decimal("0.00"))

