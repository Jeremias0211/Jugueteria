from django import forms
from django.contrib.auth.models import User, Group
from .models import Producto, ComercioConfig, Caja


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


class ComercioConfigForm(forms.ModelForm):
    class Meta:
        model = ComercioConfig
        fields = ["razon_social", "sucursal", "domicilio"]
        widgets = {
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "sucursal": forms.TextInput(attrs={"class": "form-control"}),
            "domicilio": forms.TextInput(attrs={"class": "form-control"}),
        }


class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ["nombre", "cajero", "horario_apertura", "horario_cierre", "activa"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Caja 1"}),
            "cajero": forms.Select(attrs={"class": "form-select"}),
            "horario_apertura": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "horario_cierre": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permitir seleccionar cajeros que tengan el rol de Cajero o todos los usuarios
        try:
            grupo_cajero = Group.objects.get(name='Cajero')
            self.fields['cajero'].queryset = User.objects.filter(groups=grupo_cajero) | User.objects.filter(is_superuser=True)
        except Group.DoesNotExist:
            pass


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña"}),
        required=False
    )
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol principal",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Obtener el rol actual del usuario si tiene grupos
            current_group = self.instance.groups.first()
            if current_group:
                self.initial['rol'] = current_group
        else:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            # Asignar rol (grupo)
            rol = self.cleaned_data.get("rol")
            if rol:
                user.groups.set([rol])
        return user

