from django.shortcuts import render, redirect, get_object_or_404
from .models import Produit, Tache, Operateur, PerformanceOperateur
from .forms import ProduitForm, TacheForm, OperateurForm, CustomUserCreationForm
from .logique.principal_prog import demarrer_simulation
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
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
    
    produits = Produit.objects.filter(user=request.user)
    return render(request, 'saisie_produits.html', {'form': form, 'prodacts': produits})

@login_required
def saisie_taches(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, user=request.user)

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
        'form': form, 'produit': produit, 'taches': taches
    })

@login_required
def saisie_operateurs(request):
    if request.method == 'POST':
        request.session['mode'] = 'manuel'
        form_operateur = OperateurForm(request.POST)

        all_taches = Tache.objects.all()
        performances = []

        for tache in all_taches:
            valeur_str = request.POST.get(f'performance_{tache.id}')
            try:
                performances.append((tache, float(valeur_str)))
            except (TypeError, ValueError):
                continue

        if form_operateur.is_valid():
            operateur = form_operateur.save()
            for tache, perf in performances:
                PerformanceOperateur.objects.create(
                    operateur=operateur, tache=tache, performance_initiale=perf
                )
            return redirect('saisie_operateurs')
    else:
        form_operateur = OperateurForm()
        all_taches = Tache.objects.all()
    
    operateurs = Operateur.objects.all()
    return render(request, 'saisie_operateurs.html', {
        'form_operateur': form_operateur,
        'taches': all_taches,
        'operateurs': operateurs
    })

@login_required
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
            key: float(request.POST.get(key, 20)) / 100
            for key in default_poids
        }
        if abs(sum(poids.values()) - 1) < 0.01:
            mode = request.session.get('mode', 'exemple')
            validation = 1 if mode == 'manuel' else 0
            data = demarrer_simulation(validation, poids, request.user)
            return render(request, 'simulation/resultats.html', {
                'gantt_data_json': json.dumps(data['gantt']),
                'performance_data_json': json.dumps(data['performances']),
                'makespan': data['performances']['makespan'],
                'evolution_taches': data['performances']['evolution_taches'],
                'cout_total': data['performances']['cout_total'],
                'mode': mode
            })
        else:
            message = "La somme des poids doit être exactement 100%."

    champs = [
        {'name': key, 'label': key.replace("_", " ").title(), 'value': val}
        for key, val in default_poids.items()
    ]

    return render(request, 'poids.html', {'champs': champs, 'message': message})

def exemple_simulation(request):
    if request.method == 'POST' and 'exemple' in request.POST:
        request.session['mode'] = 'exemple'
        return redirect('config_poids')

def home(request):
    return render(request, 'home.html')

def exemple_detaille(request):
    get_token(request)
    return render(request, 'exemple_detaille.html')

@login_required
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, user=request.user)
    produit.delete()
    return redirect('saisie_produits')

@login_required
def supprimer_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id)
    produit_id = tache.produit.id
    if tache.produit.user != request.user:
        return redirect('home')
    tache.delete()
    return redirect('saisie_taches', produit_id=produit_id)

@login_required
def apercu_donnees(request):
    produits = Produit.objects.filter(user=request.user).prefetch_related('taches')
    operateurs = Operateur.objects.all()
    performances = PerformanceOperateur.objects.select_related('operateur', 'tache', 'tache__produit')
    return render(request, 'apercu_donnees.html', {
        'produits': produits,
        'operateurs': operateurs,
        'performances': performances
    })

@login_required
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

@login_required
def modifier_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id)
    if tache.produit.user != request.user:
        return redirect('home')

    if request.method == 'POST':
        form = TacheForm(request.POST, instance=tache)
        if form.is_valid():
            form.save()
            return redirect('apercu_donnees')
    else:
        form = TacheForm(instance=tache)
    return render(request, 'modifier_tache.html', {'form': form, 'tache': tache})

@login_required
def supprimer_produit_apercu(request, produit_id):
    return supprimer_produit(request, produit_id)

@login_required
def supprimer_tache_apercu(request, tache_id):
    return supprimer_tache(request, tache_id)

@login_required
def modifier_operateur(request, operateur_id):
    operateur = get_object_or_404(Operateur, id=operateur_id)
    if request.method == 'POST':
        form = OperateurForm(request.POST, instance=operateur)
        if form.is_valid():
            form.save()
            return redirect('apercu_donnees')
    else:
        form = OperateurForm(instance=operateur)
    return render(request, 'modifier_operateur.html', {'form': form, 'operateur': operateur})

@login_required
def supprimer_operateur(request, operateur_id):
    operateur = get_object_or_404(Operateur, id=operateur_id)
    operateur.delete()
    return redirect('apercu_donnees')
