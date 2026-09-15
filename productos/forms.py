from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "precio", "stock", "codigo_barra"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Ej: Auto a fricción",
            }),
            "precio": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0",
            }),
            "stock": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "0", "min": "0",
            }),
            "codigo_barra": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Escaneá o escribí el código",
                "id": "id_codigo_barra",
            }),
        }

    def clean_codigo_barra(self):
        codigo = self.cleaned_data.get("codigo_barra")
        return codigo or None
