from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Produit, Tache, Operateur, PerformanceOperateur

admin.site.register(Produit)
admin.site.register(Tache)
admin.site.register(Operateur)
admin.site.register(PerformanceOperateur)