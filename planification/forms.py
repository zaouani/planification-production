from django import forms
from .models import Produit, Tache, Operateur, PerformanceOperateur
from django.forms import modelformset_factory


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
                'style': 'width: 80px;'
            }),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'ordre': "Définissez l'ordre d'exécution de cette tâche dans le processus",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

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