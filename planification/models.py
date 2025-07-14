from django.db import models
from django.contrib.auth.models import User
from django.db import models

class Produit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_produit = models.CharField(max_length=50, unique=True)
    cr = models.CharField(max_length=50)
    quantite = models.IntegerField()
    def __str__(self):
        return f"{self.id_produit} - CR: {self.cr}"

class Tache(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='taches') 
    id_tache = models.CharField(max_length=50)  
    description = models.CharField(max_length=200)
    machine = models.CharField(max_length=50) 
    temps_standard = models.FloatField(help_text="Temps standard en minutes")
    ordre = models.PositiveIntegerField(
        verbose_name="Ordre/Phase",
        help_text="Numéro d'ordre dans le processus (1, 2, 3...)",
        default=1
    )
    class Meta:
        ordering = ['ordre']
        unique_together = ('produit', 'id_tache')  
    def __str__(self):
        return f"{self.produit.id_produit}.{self.id_tache} - {self.description}"

class Operateur(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_operateur = models.CharField(max_length=50, unique=True)
    lc = models.FloatField(help_text="Learning Curve (%)")
    fc = models.FloatField(help_text="Facteur de charge (%)")
    
    def __str__(self):
        return f"{self.id_operateur}"

class PerformanceOperateur(models.Model):
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE)
    performance_initiale = models.FloatField(help_text="Performance initiale (temps en minutes)")
    
    class Meta:
        unique_together = ('operateur', 'tache')
    
    def __str__(self):
        return f"{self.operateur} - {self.tache}: {self.performance_initiale} min"