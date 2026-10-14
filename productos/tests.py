from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from productos.models import Producto, ComercioConfig, Caja


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

