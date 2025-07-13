import math
import heapq
import numpy as np
import itertools
import random


# 1. Structures de données

class Operator:
    instances = []
    
    def __init__(self, op_id, learning_params, initial_performance):
        self.id = op_id
        self.learning_params = learning_params  # {'LC': float, 'FC': float}
        self.performancess   = initial_performance  # Dict: {tache_id: performance}
        self.taches_affectees = {}  # {ordre: tache_id}
        self.machine_actuelle = None
        self.tache_actuellee=None
        self.historique_performance = []  #  Suivi temporel [[(tache,per,temps)...x24taches]....xnombre de taches assignees)]
        self.historique_travail = []      #  [(tache_id, début, fin)]
        self.temps_travail=0           #  Pour l'équité
        self.derniere_execution = {}      #  {tache_id: timestamp}
        Operator.instances.append(self)
    
    def mettre_a_jour_performance(self, tache_d,temps,simulation):
        # Paramètres fixes
        P_max = 1.15  # Performance maximale théorique
        P_min = 0.3   # Performance minimale théorique
        # Applique effet d'apprentissage/oubli
        for tache_id in self.performancess  :
            performance_actuelle=self.performancess[tache_id]
            performance_actuellee=1
            # 1. Enregistrement dans l'historique avant modification
            self.historique_performance.append((tache_id, performance_actuelle,simulation.temps_actuel))
             
            # 2. Calcul des indicateurs clés
            X = self.compter_repetitions(tache_id)  # Nombre de répétitions
            Y = self.calculer_interruption(tache_id,simulation)  # Temps d'inactivité (jours)
            # 3. Application sélective des effets
            
             # Sécurité pour les calculs exponentiels
            def safe_exp(x, max_val=700):
                return math.exp(max(min(x, max_val), -max_val))
            # Effet d'APPRENTISSAGE (équation 3)
            if X > 0:
                T_learned = min(self.temps_total_passe(tache_id), 10000)  # Temps cumulé sur la tâche
                Md = T_learned/2
                s = self.learning_params['LC']  # Taux d'apprentissage
                performance_actuellee  =self.calculate_learning_effect(X, performance_actuelle , P_max,s, T_learned, Md)
                performance_actuelleee  = max(P_min, min(P_max, performance_actuellee  ))
                self.performancess[tache_id] = performance_actuelleee
            # Effet d'OUBLI (équation 4) si inactif > 1 jour
            elif Y>0:
                    F = self.learning_params['FC']  # Taux d'oubli
                    Sd = 0.1
                    P_last = self.derniere_execution.get(tache_id, {}).get('performance', P_min)
                    performance_actuellee   =self.calculate_forgetting_effect(Y, P_last, P_min, F, Sd)
                    # 4. Contraintes de performance
                    performance_actuelleee  = max(P_min, min(P_max, performance_actuellee  ))
                    self.performancess[tache_id] = performance_actuelleee
            if tache_id==tache_d:
                self.derniere_execution[tache_id] = {'temps': temps, 'performance': performance_actuelle}

    def calculate_learning_effect( self,  n, P_previous, P_max=1.15, S=0.1, T_learned=1, Md=0.5):
        """
        Calcule la performance d'un opérateur après n répétitions selon la formule d'apprentissage.
        
        Version sécurisée qui évite les overflows.
        """
        try:
            exponent = S * (T_learned - Md)
            
            # Limiter la valeur de l'exposant pour éviter les overflows
            if exponent > 700:  # math.exp(709) est le maximum avant overflow
                exponent = 700
            elif exponent < -700:
                exponent = -700
                
            denominator = 1 - math.exp(exponent)
            
            # Éviter la division par zéro
            if abs(denominator) < 1e-10:
                return P_max
                
            P_n = P_previous + (P_max - P_previous) / denominator
            
            # Appliquer les contraintes de performance
            return 1.15
            
        except:
            # En cas d'erreur inattendue, retourner une valeur par défaut
            print('Erreur de calcule')
            return P_previous
    
    def calculate_forgetting_effect(self, t, P_last, P_min, F=0.1, Sd=1.0):
        """
        Calcule la performance d'un opérateur après une période d'inactivité selon la formule d'oubli.
        
        Paramètres:
        t (float): Temps d'inactivité écoulé
        P_last (float): Dernière performance avant la pause
        P_min (float): Performance minimale atteignable (défaut: 0.3)
        F (float): Taux d'oubli de l'opérateur (défaut: 0.1)
        Sd (float): Seuil dynamique marquant le début de l'oubli (défaut: 1.0)
        
        Retourne:
        float: Nouvelle performance P(t) (bornée entre P_min et 1.15)
        """
        # Calcul de la performance selon la formule d'oubli
        denominator = 1 - math.exp(F * (t - Sd))
        if denominator == 0:
            P_t = P_min  # Éviter la division par zéro
        else:
            P_t = P_min + (P_last - P_min) / denominator
        
        # Application des contraintes de performance
        P_t = max(P_min, min(P_t, 1.15))  # Bornée entre 0.3 et 1.15
        
        return P_t

    def get_gantt_data(self):
            """Retourne les plages horaires pour le Gantt"""
            data = []
            
            for tache_id, debut, fin in self.historique_travail:
                if  fin:
                    
                    data.append({
                        'Tache': tache_id,
                        'Début': debut,
                        'Fin': fin,
                        'Machine': self.machine_actuelle
                    })
                else: print(debut,fin)
            
            return data

    def temps_total_passe(self, tache_id):
        """Calcule le temps cumulé passé sur une tâche"""
        for tache in Task.instances:
            if tache.id==tache_id:
                return tache.temps_reel
        return 0

    def demarrer_tache(self, tache, temps_debut):
        self.historique_travail.append((tache.id, temps_debut, None))
    
    def terminer_tache(self, temps_fin):
        if self.historique_travail:
            debut = self.historique_travail[-1][1]
            self.historique_travail[-1] = (self.historique_travail[-1][0], debut, temps_fin)
   
    def compter_repetitions(self,tache_id):
        nembre_repition=0
        if tache_id == self.tache_actuellee .id:
            nembre_repition=self.tache_actuellee.nembre_repition
        return nembre_repition
    
    def calculer_interruption(self, tache_id,simulation):
        """
        Calcule la durée d'interruption depuis la dernière exécution de cette tâche
        """
        # 1. Si la tâche n'a jamais été exécutée, interruption = 0
        duree_jours=0
        if tache_id != self.tache_actuellee.id:
            if tache_id in self.derniere_execution:
                # 2. Récupérer le timestamp de la dernière exécution
                derniere_date = self.derniere_execution[tache_id]['temps']
                # 3. Calculer la durée écoulée (en jours)
                duree_jours = (simulation.temps_actuel - derniere_date) / (60 * 8)  
            else:
                 duree_jours = simulation.temps_actuel / (60 * 8)  
        # 4. L'oubli ne s'active qu'après 1 jour complet
        return max(0, duree_jours - 1)

class Product:
    instances = []
    
    def __init__(self, pid, tasks, std_times, quantity, cr, machines_requises):
        self.id = pid
        self.tasks = tasks  # Liste des tâches [T1, T2, ...]
        self.std_times = std_times  # {tache_id: temps}
        self.quantity = quantity
        self.cr = cr  # Coût de sous-performance
        self.nembre_repition=quantity
        self.machines_requises = machines_requises  # NEW: {tache_id: machine_id}
        self.quantite_restante = quantity  # NEW: Suivi par tâche
        Product.instances.append(self)
        if quantity <= 0:
            raise ValueError("La quantité doit être positive.")
    def __str__(self):
        return f"{self.id}"  # <-- Si cette méthode existe, modifiez-la    

class Task:
    instances = []
    
    def __init__(self, tid, product, phase, precedence=None):
        self.id = tid
        self.product = product
        self.phase = phase
        self.precedence = precedence  # Task précédente (si phase > 1)
        self.temps_standard = product.std_times[tid]
        self.machines_compatibles= product.machines_requises[tid]
        self.machine_requise = self.determiner_machine()
        self.operateur_affecte = None
        self.temps_debut = None
        self.temps_fin = 0
        self.temps_restant=0
        self.quantite=product.quantity
        self.nembre_repition=product.nembre_repition
        self.next_tasks = []
        self.temps_reel=0
        self.temps_attente=0
        self.cr=product.cr
        self.quantite_restante=product.quantity
        Task.instances.append(self)
        self.est_en_cours=False
    def ajouter_next_task(self, task):
        self.next_tasks.append(task)
    def __eq__(self, other):
        """Compare les tâches par leur ID"""
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        """Permet d'utiliser les Task dans des sets/dicts"""
        return hash(self.id)

    def __repr__(self):
        """Représentation claire pour le débogage"""
        return f"Task(id={self.id}, product={self.product.id}, phase={self.phase})"

    def determiner_machine(self):
        machine = self.machines_compatibles[0]

        if len(self.machines_compatibles) > 1 and Simulation.instances:
            for machine_ in self.machines_compatibles:
                if self.calculer_temps_restant(machine_) < self.calculer_temps_restant(machine):
                    machine = machine_
        return machine

    def calculer_temps_restant(self, machine):
        temps_restant = 0
        if machine.tache_actuelle and Simulation.instances:
            temps_actuel = Simulation.instances[0].temps_actuel
            temps_restant = max(0, machine.tache_actuelle.temps_fin - temps_actuel)
        return temps_restant
      
class Machine:
    instances = []
    
    def __init__(self, mid, taches_compatibles):
        self.id = mid
        self.taches_compatibles = taches_compatibles  # Liste des tâches pouvant être exécutées
        self.tache_en_attente=[]
        self.tache_actuelle = None
        self.historique = []  # [(tache_id, op_id, début, fin)]
        self.temps_setup = 0  # Temps de changement de tâche
        Machine.instances.append(self)
    
    def demarrer_tache(self, tache):
        if self.tache_actuelle:
            self.temps_setup = 5  # Ex: 5 min de setup
        self.tache_actuelle = tache
    def determiner_tache(self):
        tache=None
        if self.tache_en_attente:
            tache=self.tache_en_attente.pop(0)
        return tache
    
    def get_gantt_data(self):
        data = []
        for tache_id, op_id, debut, fin in self.historique:
            data.append({
                'Tache': tache_id,
                'Opérateur': op_id,
                'Début': debut,
                'Fin': fin
            })
        return data
    
class Ordonnanceur:
    def __init__(self, poids_cout=0.4, poids_equite=0.2, poids_makespan=0.2, poids_performance=0.2,poids_penalite_attente=0.5):
        self.poids = {
            "cout": poids_cout,
            "equite": poids_equite,
            "makespan": poids_makespan,
            "performance": poids_performance,
            "penalite_attente":poids_penalite_attente
        }
#methodes de selection       
    def choisir_tache(self, operateur, simulation,tache_finie):
        scores = []
        taches_disponibles=self.taches_disponibles_pour_operateur(operateur, simulation)
        # 1. Évaluer les tâches disponibles classiques
        for tache in taches_disponibles:
            tache.temps_attente=0
            score = self._calculer_score(operateur, tache, simulation, temps_attente=0)
            scores.append((score, tache))
       
            
        # 2. Évaluer les tâches non disponibles (avec temps d'attente estimé)
        taches_no_disponibles=self.taches_non_disponibles(simulation)
        for dic in taches_no_disponibles:
            score = self._calculer_score(operateur, dic['tache'], simulation, temps_attente=dic['temps_restant'])
            scores.append((score, dic['tache'], dic['temps_restant']))

        # 3. Sélectionner la meilleure option
        if not scores:
            return None
        # Priorité aux tâches disponibles (temps_attente=0) si score similaire
        meilleure_option = max(scores, key=lambda x: (x[0], -x[2] if len(x) > 2 else 0))
        '''existe = any(tache.id == next_task.id for (score, tache,x) in scores)
        if existe:
            return next_task'''
        meilleure_op=meilleure_option[1]
        for dic in taches_no_disponibles:
            if meilleure_op.id==dic['tache'].id:
                meilleure_op.temps_attente=dic['temps_restant']
        print('taches en cours',list(tache.id for tache in Task.instances if tache.est_en_cours))
        return meilleure_op 
    
    def affecter_tache(self, operateur, tache, simulation):
        """
        - Le séquençage des tâches
        - Les quantités de production
        - L'épuisement des tâches
        """
        # 1. Vérifier que la tâche est la prochaine logique et disponible
        if not tache.quantite_restante > 0:
            return False
        
        # 2. Calcul du temps pour toute la quantité
        quantite = tache.quantite
        temps_unitaire = tache.temps_standard + tache.temps_standard*(1- operateur.performancess [tache.id])
        temps_real = temps_unitaire * quantite 
        print('le temps d attente ',tache.temps_attente)
        # 3. Marquage comme complètement réservée
        tache.est_en_cours = True
        tache.quantite_restante = 0  # Épuise immédiatement la quantité

        # 4. Mise à jour des états
        temps_debut=simulation.temps_actuel+tache.temps_attente
        operateur.tache_actuellee= tache
        operateur.taches_affectees[len(operateur.taches_affectees)+1]=tache.id
        if tache.temps_attente>0:
            tache.machine_requise.tache_en_attente.append(tache)
        else:tache.machine_requise.tache_actuelle = tache

        tache.operateur_affecte = operateur
        tache.temps_debut = simulation.temps_actuel
        tache.temps_fin = temps_debut + temps_real
        tache.temps_reel=temps_real
        temps_fin=tache.temps_fin
        operateur.historique_travail.append((tache.id,temps_debut,temps_fin))
        machine =tache.machine_requise
        machine.historique.append((tache.id,operateur.id,temps_debut,temps_fin))
        operateur.machine_actuelle=machine.id

        # 5. Création des événements
        simulation.ajouter_evenement(Evenement(
            temps=temps_debut,
            type="DEBUT_TACHE",
            tache=tache,
            operateur=operateur,
            machine=tache.machine_requise
        ))

        simulation.ajouter_evenement(Evenement(
            temps=temps_fin,
            type="FIN_TACHE",
            tache=tache,
            operateur=operateur,
            machine=tache.machine_requise
        ))

        print(f"[AFFECTATION] {operateur.id} → {tache.id} ({tache.product.id}) "
            f"Quantité:{quantite} | Temps:{temps_real:.1f}min | "
            f"Fin à t={tache.temps_fin:.1f}")
        
        return True

    def terminer_tache(self, tache, simulation):
        """Version corrigée de la fin de tâche"""
        # 1. Mettre à jour le makespan
        simulation.makespan_actuel = max(simulation.makespan_actuel, simulation.temps_actuel)
        # 1. Libération des ressources
        tache.machine_requise.tache_actuelle = tache.machine_requise.determiner_tache()
        tache.operateur_affecte.tache_actuelle = None
        tache.est_en_cours = False
        simulation.termines.add(tache)
        print('les taches terminees',list(tache.id for tache in simulation.termines))

        '''# 2. Trouver la tâche suivante dans le workflow
        next_task = self._trouver_tache_suivante(tache)
        
        if next_task:
            # 3. Préparer l'affectation si possible
            if (self._tache_eligible(tache.operateur_affecte, next_task) and
                self._machine_disponible(next_task)):
                
                self.affecter_tache(tache.operateur_affecte, next_task, simulation)
            else:
                print(f"[ATTENTE] Suite du workflow {tache.product.id} bloquée")'''
    
    def _trouver_tache_suivante(self, tache):
        """Trouve la prochaine tâche dans le workflow du produit"""
        product = tache.product
        current_index = product.tasks.index(tache.id)
        
        if current_index + 1 < len(product.tasks):
            next_task_id = product.tasks[current_index + 1]
            return next(t for t in Task.instances if t.id == next_task_id)
        return None

    def _preparer_affectation(self, operateur, next_task, simulation):
        """Prépare l'affectation de la tâche suivante"""
        if (next_task and 
            self._tache_eligible(operateur, next_task) and 
            self._machine_disponible(next_task)):
            self.affecter_tache(operateur, next_task, simulation)    

#methodes de calcules
    def _calculer_score(self,operateur, tache, simulation, temps_attente):
        score = 0
        # Calcul des scores bruts
        cout_brut = self._calculer_cout(operateur, tache)         
        perf_brut = self._calculer_performance(operateur, tache)  
        equite_brut = self._calculer_equite(operateurs=Operator.instances)
        makespan_brut = self._calculer_makespan(operateur,simulation, tache)
        # Normalisation des scores bruts
        score_cout = self._normaliser_cout(cout_brut)              
        score_perf = self._normaliser_performance(perf_brut)       
        score_equite=self._normaliser_equite(equite_brut)
        score_makespan = self._normaliser_makespan(makespan_brut)
        
        # Combinaison pondérée
        score_total = (
            self.poids["cout"] * score_cout +
            self.poids["performance"] * score_perf+
            self.poids["equite"] * score_equite +
            self.poids["makespan"] * score_makespan-
            self.poids["penalite_attente"] * (temps_attente / simulation.temps_max)
        )
        score=score_total
        return score

    def _calculer_performance(self, operateur, tache):
        """
        Score basé sur la performance passée de l'opérateur sur cette tâche.
        Plus la performance est élevée, meilleur est le score.
        """
        # Récupère la performance moyenne historique (ex: moyenne des 5 dernières exécutions)
        performances = [hist[1] for hist in operateur.historique_performance 
                       if hist[0] == tache.id]
        perf_moyenne = sum(performances) / len(performances) if performances else operateur.performancess.get(tache.id, 0.1)
        
        return perf_moyenne 

    def _calculer_equite(self, operateurs):
        """
        Calcule un score d'équité basé sur l'écart de charge entre opérateurs.
        Retourne un score normalisé entre 0 (inéquité max) et 1 (équité parfaite).
        """
        # 1. Récupérer les temps de travail de chaque opérateur
        temps_travail = [op.temps_travail for op in operateurs]
        
        if not temps_travail:
            return 1.0  # Cas par défaut si aucun opérateur
        
        # 2. Calculer l'écart-type (mesure d'inéquité)
        ecart_type = np.std(temps_travail)
        
        # 3. Normalisation inverse (1 - valeur normalisée)
        max_ecart = max(temps_travail) - min(temps_travail) if len(temps_travail) > 1 else 0
        max_theorique = 500  # Exemple: valeur maximale estimée pour votre simulation
        score = 1 - (ecart_type / max_theorique)
        
        # 4. Bornage entre 0 et 1
        return max(0.0, min(1.0, score))
    
    def _calculer_cout(self, operateur, tache):
        """
        Calcule un score inversé du coût de sous-performance.
        Plus le score est élevé, moins la tâche coûte cher.
        """
        # 1. Calcul du temps réel (incluant la performance)
        temps_reel = tache.temps_standard / operateur.performancess [tache.id]
        
        # 2. Sous-performance (écart entre réel et standard)
        sous_performance = temps_reel - tache.temps_standard
        
        # 3. Coût monétaire
        cout = sous_performance * tache.product.cr  # cr = coût par minute
        
        # 4. Normalisation inverse
        cout_max = 1000  # Seuil de coût maximum estimé
        score = 1 - (cout / cout_max)
        
        return max(0.0, min(1.0, score))
    
    def _calculer_makespan(self,operateur, simulation, tache):
        """
        Calcule un score inversement proportionnel à l'impact sur le makespan.
        Plus le score est élevé, moins la tâche rallonge le planning global.
        """
        # 1. Temps de fin estimé si on ajoute cette tâche
        temps_fin_estimé = simulation.temps_actuel + (tache.temps_standard / operateur.performancess[tache.id])
        
        # 2. Comparaison avec le makespan courant
        makespan_courant = simulation.makespan_actuel
        impact = temps_fin_estimé - makespan_courant
        
        # 3. Normalisation (ex: 1 = pas d'impact, 0 = impact sévère)
        impact_max = 240  # Exemple: 4h d'impact maximum toléré
        score = 1 - (impact / impact_max)
        return max(0.0, min(1.0, score))
    #ajouter temps de reglage 
    def _estimer_temps_attente(self, tache, simulation,Machine):
        """Calcule le temps avant qu'une tâche non disponible soit libérée"""
        if self._machine_disponible( tache):
            if tache.precedence and tache.precedence not in simulation.termines:
                # Cas 1: Attente due à une tâche de précédence non terminée
                if tache.precedence.operateur_affecte != None:
                    return tache.precedence.temps_fin-simulation.temps_actuel+1
                return 0
        else:
            # Cas 2: Attente due à une machine occupée
            machine=tache.machine_requise
            if machine.tache_actuelle:
                if not  machine.tache_en_attente:
                    if (not tache.precedence) or (tache.precedence and tache.precedence in simulation.termines):
                        machine = tache.machine_requise
                        return machine.tache_actuelle.temps_fin- simulation.temps_actuel+1
                else: 
                    return machine.tache_en_attente[-1].temps_fin - simulation.temps_actuel + 1
            elif machine.tache_en_attente:
                return machine.tache_en_attente[-1].temps_fin - simulation.temps_actuel + 1
            else:
                print('probleeeeeeeeeeeemmmmmmmmmmm')
        return 0 # Si l'attente est indeterminée

    def mise_a_jour_qntt_prod(self,tache):
        tem=0
        for tache_id in tache.product.tasks:
            for task in Task.instances:
                if tache_id == task.id:
                    tem+=task.quantite
        if tem==0:
            tache.produit.quantity=0
        return True
    
#methode de normalisation 
    def _normaliser_cout(self, score_cout_brut):
        """Transforme un coût à minimiser en score à maximiser."""
        # Exemple de normalisation linéaire (à adapter selon vos données)
        cout_max = 1000  # Valeur maximale estimée
        cout_min = 0      # Valeur minimale théorique
        return 1 - (score_cout_brut - cout_min) / (cout_max - cout_min)  # Inversion + normalisation

    def _normaliser_makespan(self, makespan_brut):
        """
        Normalise le makespan entre 0 (pire) et 1 (meilleur)
        
        Args:
            makespan_brut: Valeur réelle du makespan courant
            
        Returns:
            float: Score normalisé
        """
        min_m, max_m = self._calculer_bornes_makespan(Product.instances,Operator.instances)
        
        # Formule de normalisation
        score = 1 - (makespan_brut - min_m) / (max_m - min_m + 1e-6)  # +1e-6 évite division par zéro
        
        # Bornage entre 0 et 1
        return max(0, min(1, score))

    def _calculer_bornes_makespan(self, produits, operateurs):
        """
        Calcule les bornes min/max théoriques du makespan
        
        Args:
            produits: Liste des produits à produire
            operateurs: Liste des opérateurs disponibles
        
        Returns:
            tuple: (makespan_min_theorique, makespan_max_estime)
        """
        # 1. Calcul du makespan minimal théorique (meilleur cas possible)
        temps_total_taches = sum(
            sum(tache.temps_standard for tache in Task.instances if tache.product == prod)
            for prod in produits
        )
        makespan_min_theorique = temps_total_taches / len(operateurs)
        
        # 2. Estimation du makespan maximal (pire cas réaliste)
        temps_par_operateur = []
        for op in operateurs:
            temps_op = sum(
                tache.temps_standard / op.performancess.get(tache.id, 0.35)  # 0.35 = perf minimale
                for prod in produits 
                for tache in Task.instances 
                if tache.product == prod and tache.id in op.performancess
            )
            temps_par_operateur.append(temps_op)
        
        makespan_max_estime = max(temps_par_operateur) * 1.5  # Marge de sécurité
        
        # 3. Ajustement des bornes
        makespan_min_theorique = max(1, makespan_min_theorique)  # Éviter division par zéro
        makespan_max_estime = max(makespan_min_theorique * 2, makespan_max_estime)
        
        return makespan_min_theorique, makespan_max_estime

    def _normaliser_performance(self, perf_brute):
        """Performance est déjà dans [0, 1.15] -> on la ramène à [0, 1]"""
        return perf_brute / 1.15
    
    def _normaliser_equite(self, equite_brut, min_equite=0, max_equite=1):
        """
        Normalise le score d'équité brut entre 0 et 1.
        - equite_brut : Mesure actuelle de l'inéquité (ex: écart-type des temps de travail)
        - min_equite : Valeur minimale théorique (parfaite équité)
        - max_equite : Valeur maximale estimée (pire cas d'inéquité)
        """
        # Si equite_brut est une mesure d'inéquité (à minimiser) :
        score_normalise = 1 - (equite_brut - min_equite) / (max_equite - min_equite + 1e-6)  # +1e-6 évite la division par zéro
        
        # Borne entre 0 et 1
        return max(0, min(1, score_normalise))

#methodes de disponibilite
    def taches_disponibles_pour_operateur(self, operateur, simulation):
        
        liste= [
            tache for tache in Task.instances
            if self._tache_eligible(operateur, tache)
            and self._est_prochaine_tache_logique(tache, simulation)
            and self._machine_disponible(tache)
            and tache.quantite_restante > 0
        ]
        print('tache disponible',list(tache.id for tache in liste))
        return liste

    def _est_prochaine_tache_logique(self, tache, simulation):
        """
        Vérifie si c'est la prochaine tâche à faire dans le workflow du produit
        """
        # Si c'est une tâche initiale, toujours valide
        if tache.precedence is None:
            return True
            
        # Vérifie si la tâche précédente est terminée
        elif tache.precedence in simulation.termines:
            return True
        return False
    
    def _tache_eligible(self, operateur, tache):
        return (
            tache.id in operateur.performancess# L'opérateur sait faire cette tâche
            and operateur.performancess  [tache.id] >= 0.2  # Performance minimale requise
        )
   
    def _machine_disponible(self, tache):
        machine=tache.machine_requise
        if not machine.tache_en_attente and not machine.tache_actuelle:
                return True
        return False  # Si aucune machine n'est compatible

    def taches_non_disponibles(self, simulation):
        taches_bloquees = []
        for tache in Task.instances:
            if tache.quantite_restante>0:
                # Trouver la machine compatible
                machine = tache.machine_requise
                if not machine:
                        print('aucune machine compatible') 
                # Calcul du temps restant si simulation est disponible
                temps_restant = self._estimer_temps_attente( tache, simulation,Machine)
                if temps_restant>0:
                            taches_bloquees.append({
                                'tache': tache,
                                'temps_restant': temps_restant
                            })
        print('tache non disponible',list(dic['tache'].id for dic in taches_bloquees))
        return taches_bloquees

class Simulation:
    instances=[]
    def __init__(self):
        self.temps_actuel = 1  # Temps écoulé depuis le début (en minutes)
        self.evenements = []    # File d'événements triés par temps (min-heap)
        self.makespan_actuel = 1  # Durée totale estimée du planning
        self.termines = set()   # Tâches terminées (pour vérifier les précédences)
        self.historique = []    # Journal des événements pour analyse
        self.temps_max=1440
        Simulation.instances.append(self)
    def ajouter_evenement(self, evenement):
        """Ajoute un événement à la file de priorité."""
        heapq.heappush(self.evenements, (evenement.temps, evenement))

    def obtenir_prochain_evenement(self):
        """Récupère l'événement le plus imminent."""
        if self.evenements:
            return heapq.heappop(self.evenements)[1]  # (temps, Evenement)
        return None
  
    def est_terminee(self, tache):
        """Vérifie si une tâche est dans les terminées."""
        return tache in self.termines
    
    def _traiter_evenement(self, evenement):
        if evenement.type == "FIN_TACHE":
            self.makespan_actuel = max(self.makespan_actuel, self.temps_actuel)
    
class Evenement:
    def __init__(self, temps, type, tache=None, operateur=None, machine=None):
        self.temps = temps      # Date d'exécution (en minutes)
        self.type = type        # "DEBUT_TACHE", "FIN_TACHE", "PAUSE", etc.
        self.tache = tache      # Objet Task concerné
        self.operateur = operateur  # Objet Operator impliqué
        self.machine = machine  # Objet Machine concernée (optionnel)

    def __lt__(self, other):
        """Permet la comparaison pour la file de priorité."""
        return self.temps < other.temps

class Cout:
        def __init__(self):
            self.total_sous_performance = 0  # Coûts cumulés en euros
            self.par_operateur = {}          # Ex: {"O1": 250, "O2": 180}
            self.par_tache = {}              # Ex: {"T111": 120, "T112": 95}
            self.par_produit = {}            # Ex: {"P1": 300, "P2": 150}
            self.historique = []             # Historique des coûts (timestamp, montant, type)

        def ajouter_cout(self,simulation, sous_performance, cr, operateur=None, tache=None):
            """
            Ajoute un coût de sous-performance au système
            """
            # Calcul du coût monétaire
            if cr==0:
                cr==1
            cout = sous_performance * cr
            
            # Mise à jour des totaux
            self.total_sous_performance += cout
            
            # Mise à jour par opérateur
            if operateur:
                self.par_operateur[operateur.id] = self.par_operateur.get(operateur.id, 0) + cout
                
            # Mise à jour par tâche
            if tache:
                self.par_tache[tache.id] = self.par_tache.get(tache.id, 0) + cout
                self.par_produit[tache.product.id] = self.par_produit.get(tache.product.id, 0) + cout
            
            # Enregistrement historique
            self.historique.append({
                'temps':  simulation.temps_actuel ,
                'montant': cout,
                'type': 'sous_performance',
                'operateur': operateur.id if operateur else None,
                'tache': tache.id if tache else None
            })
        def generer_rapport(self):
            """Retourne un résumé des coûts."""
            return {
                "total": self.total_sous_performance,
                "par_operateur": self.par_operateur,
                "par_tache": self.par_tache
            }

class CombinationGenerator:
    def __init__(self, operators):
        self.operators = operators
        self.all_combinations = list(itertools.permutations(operators))
        random.shuffle(self.all_combinations)  # Mélange aléatoire
        self.index = 0
    
    def get_unique_combination(self):
        if self.index >= len(self.all_combinations):
            raise StopIteration("Toutes les combinaisons ont été épuisées")
        
        combination = self.all_combinations[self.index]
        self.index += 1
        return combination

    def reset(self):
        """Réinitialise le générateur"""
        random.shuffle(self.all_combinations)
        self.index = 0
