# Sistema de Gestión para Juguetería — Módulo de Carga de Productos

Funcionalidad desarrollada: **alta de productos con carga de código de barras
desde el celular**, correspondiente al caso de uso "Registrar Ingreso de
Mercadería" (rol Depósito).

Coherente con el DER / diagrama de clases entregados: el modelo `Producto`
usa los mismos campos (`nombre`, `precio`, `stock`) más `codigo_barra`
(necesario para el escaneo).

Stack: Python + Django + SQLite + Bootstrap — el mismo elegido en la
planificación de desarrollo del proyecto.

## 1. Instalar y correr (en la notebook)

Requisito: tener Python 3.10 o superior instalado.

```bash
# 1) entrar a la carpeta del proyecto
cd jugueteria_productos

# 2) crear un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3) instalar dependencias
pip install -r requirements.txt

# 4) crear la base de datos (ya viene con migraciones y datos de ejemplo)
py manage.py migrate

# 5) levantar el servidor, accesible desde toda la red Wi-Fi
py manage.py runserver
```

Abrir en la notebook: **http://127.0.0.1:8000/**

Ya viene con 3 productos de ejemplo cargados (para no arrancar con la
tabla vacía) y un usuario de administrador: `admin` / `jugueteria2026`
en **http://127.0.0.1:8000/admin/**.

## 2. Probar el escaneo de código de barras desde el celular

1. Conectá el celular a la **misma red Wi-Fi** que la notebook.
2. Fijate la IP de la notebook:
   - Windows: `ipconfig` (buscar "Dirección IPv4", ej. `192.168.0.15`)
   - Mac/Linux: `ifconfig` o `ip a`
3. En el navegador del celular entrá a `http://<esa-IP>:8000/` (ej.
   `http://192.168.0.15:8000/`).
4. Tocá el botón **"📷 Escanear"**: se abre la cámara del celular para
   sacarle una foto al código de barras. La lectura se hace ahí mismo en
   el navegador (librería `html5-qrcode`) y completa el campo solo.
5. Si algún código no se lee bien (foto borrosa, poca luz), se puede
   escribir a mano sin problema — el campo es editable.

> **Nota técnica para la defensa oral:** el escaneo usa la cámara vía un
> `<input type="file" capture="environment">`, que funciona sobre HTTP
> normal en la red local (no requiere HTTPS). Existe también un modo de
> **cámara en vivo** con la misma librería (`Html5QrcodeScanner`), más
> parecido a un lector de supermercado, pero los navegadores exigen
> HTTPS para activar la cámara en vivo fuera de `localhost` — por eso se
> optó por "sacar foto y leer" como método principal, que es más simple
> de mostrar en una demo y no depende de configurar un certificado.

## 3. Qué mostrar en la defensa oral

- El formulario de carga y la tabla de stock están en la misma pantalla
  (`productos/views.py` → `carga_productos`), como en el boceto de la
  vista de Depósito ya entregado.
- Al guardar, el producto se valida (`productos/forms.py`) y se guarda
  en la base SQLite a través del ORM de Django (`productos/models.py`),
  sin escribir SQL a mano.
- El estado del stock (OK / BAJO / SIN STOCK) se calcula solo según la
  cantidad, igual que en el boceto.
- `admin.py` expone el mismo modelo en el panel de administración de
  Django, para mostrar los datos "en crudo" si lo piden.
- El modelo coincide con la entidad PRODUCTOS del DER y del diagrama de
  clases (mismos campos + `codigo_barra`, agregado para esta entrega).

## 4. Estructura del proyecto

```
jugueteria_productos/
├── manage.py
├── requirements.txt
├── db.sqlite3                  (base con 3 productos de ejemplo)
├── jugueteria_productos/       (configuración del proyecto)
│   ├── settings.py
│   └── urls.py
└── productos/                  (la app: carga de productos)
    ├── models.py                → entidad Producto
    ├── forms.py                 → formulario de alta
    ├── views.py                 → lógica de carga y listado
    ├── admin.py                 → panel de administración
    ├── urls.py
    └── templates/productos/
        ├── base.html
        └── carga.html           → formulario + escaneo + tabla de stock
```
