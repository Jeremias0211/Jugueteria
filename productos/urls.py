from django.urls import path
from . import views

urlpatterns = [
    path("", views.carga_productos, name="carga_productos"),
    path("eliminar/<int:pk>/", views.eliminar_producto, name="eliminar_producto"),
]
