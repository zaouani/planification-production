from django.shortcuts import render, redirect, get_object_or_404
from .models import Produit, Tache, Operateur, PerformanceOperateur
from .forms import ProduitForm, TacheForm, OperateurForm, PerformanceForm
from .logique.principal_prog import demarrer_simulation
from django.middleware.csrf import get_token
from django.http import Http404
import json
### Étape 1 : Saisie du produit
def saisie_produits(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            produit = form.save(commit=False)  
            produit.user = request.user        
            produit.save()                     
            return redirect('saisie_taches', produit_id=produit.id)
    else:
        form = ProduitForm()
        
    prodacts = Produit.objects.filter(user=request.user)  
    return render(request, 'saisie_produits.html', {'form': form, 'prodacts': prodacts})

### Étape 2 : Saisie des tâches pour le produit
def saisie_taches(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if produit.user != request.user:
        raise Http404("Produit non trouvé.")
    if request.method == 'POST':
        form = TacheForm(request.POST)
        if form.is_valid():
            tache = form.save(commit=False)
            tache.produit = produit
            tache.save()
            return redirect('saisie_taches', produit_id=produit.id)
    else:
        form = TacheForm()
    taches = Tache.objects.filter(produit=produit)
    return render(request, 'saisie_taches.html', {
        'form': form,
        'produit': produit,
        'taches': taches
    })
### Étape 3 : Saisie des opérateurs et performances
def saisie_operateurs(request):
    if request.method == 'POST':
        request.session['mode'] = 'manuel'
        form_operateur = OperateurForm(request.POST)

        # Récupère uniquement les tâches de l'utilisateur connecté
        all_taches = Tache.objects.filter(produit__user=request.user)
        performances = []

        for tache in all_taches:
            valeur_str = request.POST.get(f'performance_{tache.id}')
            try:
                valeur = float(valeur_str)
                performances.append((tache, valeur))
            except (TypeError, ValueError):
                continue

        if form_operateur.is_valid():
            operateur = form_operateur.save(commit=False)
            operateur.user = request.user  
            operateur.save()

            for tache, perf in performances:
                PerformanceOperateur.objects.create(
                    operateur=operateur,
                    tache=tache,
                    performance_initiale=perf
                )

            return redirect('saisie_operateurs')
    else:
        form_operateur = OperateurForm()
        all_taches = Tache.objects.filter(produit__user=request.user)

    operateurs = Operateur.objects.filter(user=request.user)  
    return render(request, 'saisie_operateurs.html', {
        'form_operateur': form_operateur,
        'taches': all_taches,
        'operateurs': operateurs
    })

def exemple_simulation(request):
    if request.method == 'POST' and 'exemple' in request.POST:
        request.session['mode'] = 'exemple'
        return redirect('config_poids')
    
    
def config_poids(request):
    default_poids = {
        'poids_cout': 20,
        'poids_equite': 20,
        'poids_makespan': 20,
        'poids_performance': 20,
        'poids_penalite_attente': 20,
    }
    message = None  
    if request.method == 'POST':
        poids = {
            'poids_cout': float(request.POST.get('poids_cout', 20))/100,
            'poids_equite': float(request.POST.get('poids_equite', 20))/100,
            'poids_makespan': float(request.POST.get('poids_makespan', 20))/100,
            'poids_performance': float(request.POST.get('poids_performance', 20))/100,
            'poids_penalite_attente': float(request.POST.get('poids_penalite_attente', 20))/100,
        }
        total = sum(poids.values())
        if abs(total - 1) < 0.01:
            mode = request.session.get('mode', 'exemple')
            validation = 1 if mode == 'manuel' else 0


            data = demarrer_simulation(validation, poids, user=request.user)
            context = {
                
                'gantt_data_json': json.dumps(data['gantt']),
                'performance_data_json': json.dumps(data['performances']),
                'makespan': data['performances']['makespan'],
                'evolution_taches': data['performances']['evolution_taches'], 
                'cout_total': data['performances']['cout_total'],
                'mode': mode
            }

            return render(request, 'simulation/resultats.html', context)
        else:
            message = "La somme des poids doit être exactement 100%."

    else:
        poids = default_poids

    # Préparer les champs pour le formulaire
    champs = [
        {'name': 'poids_cout', 'label': 'Poids Coût', 'value': poids['poids_cout']},
        {'name': 'poids_equite', 'label': 'Poids Équité', 'value': poids['poids_equite']},
        {'name': 'poids_makespan', 'label': 'Poids Makespan', 'value': poids['poids_makespan']},
        {'name': 'poids_performance', 'label': 'Poids Performance', 'value': poids['poids_performance']},
        {'name': 'poids_penalite_attente', 'label': "Poids Pénalité d'Attente", 'value': poids['poids_penalite_attente']},
    ]

    return render(request, 'poids.html', {'champs': champs, 'message': message})

def home(request):
    return render(request, 'home.html')

def exemple_detaille(request):
    get_token(request)
    return render(request, 'exemple_detaille.html')

def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, user=request.user)
    produit.delete()
    return redirect('saisie_produits')

def supprimer_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id, produit__user=request.user)
    produit_id = tache.produit.id
    tache.delete()
    return redirect('saisie_taches', produit_id=produit_id)

def supprimer_produit_apercu(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, user=request.user)
    produit.delete()
    return redirect('apercu_donnees')

def supprimer_tache_apercu(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id, produit__user=request.user)
    produit_id = tache.produit.id
    tache.delete()
    return redirect('apercu_donnees', produit_id=produit_id)

def apercu_donnees(request):
    produits = Produit.objects.filter(user=request.user).prefetch_related('taches')
    operateurs = Operateur.objects.filter(user=request.user)
    performances = PerformanceOperateur.objects.filter(operateur__user=request.user).select_related('operateur', 'tache', 'tache__produit')
    return render(request, 'apercu_donnees.html', {
        'produits': produits,
        'operateurs': operateurs,
        'performances': performances,
    })

def modifier_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, user=request.user)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            return redirect('apercu_donnees')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'modifier_produit.html', {'form': form})


def modifier_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id, produit__user=request.user)
    if request.method == 'POST':
        form = TacheForm(request.POST, instance=tache)
        if form.is_valid():
            form.save()
            return redirect('apercu_donnees')
    else:
        form = TacheForm(instance=tache)
    return render(request, 'modifier_tache.html', {'form': form, 'tache': tache})


def modifier_operateur(request, operateur_id):
    operateur = get_object_or_404(Operateur, id=operateur_id, user=request.user)
    if request.method == 'POST':
        form = OperateurForm(request.POST, instance=operateur)
        if form.is_valid():
            form.save()
            return redirect('apercu_donnees')
    else:
        form = OperateurForm(instance=operateur)
    return render(request, 'modifier_operateur.html', {'form': form, 'operateur': operateur})


def supprimer_operateur(request, operateur_id):
    operateur = get_object_or_404(Operateur, id=operateur_id, user=request.user)
    operateur.delete()
    return redirect('apercu_donnees')