from django import forms
from .models import Produit, Tache, Operateur, PerformanceOperateur
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['id_produit', 'cr', 'quantite']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class TacheForm(forms.ModelForm):
    class Meta:
        model = Tache
        fields = ['produit', 'id_tache', 'description', 'machine', 'temps_standard', 'ordre']
        widgets = {
            'ordre': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control',
                'style': 'width: 100px;',
                'placeholder': "Définissez l'ordre d'exécution de cette tâche dans le processus"
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Décrivez brièvement cette tâche'
            }),
            'machine': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Entrez les identifiants des machines séparés par des virgules (ex: M01, M02, M07)'
            }),
            'temps_standard': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width: 120px;',
                'placeholder':"En minutes"
            }),
            'id_tache': forms.TextInput(attrs={'class': 'form-control'}),
            'produit': forms.Select(attrs={'class': 'form-control'}),
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class OperateurForm(forms.ModelForm):
    class Meta:
        model = Operateur
        fields = ['id_operateur', 'lc', 'fc']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class PerformanceForm(forms.ModelForm):
    class Meta:
        model = PerformanceOperateur
        fields = ['tache', 'performance_initiale']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})



PerformanceFormSet = modelformset_factory(
    PerformanceOperateur,
    form=PerformanceForm,  
    extra=0
)