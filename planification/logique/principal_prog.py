from .Structured_data import Operator, Product, Task, Machine, Simulation, Ordonnanceur, Cout, Evenement
from .fonctions import boucle_principale, get_data
from planification.models import Produit, Tache, Operateur, PerformanceOperateur

import logging
from django.db.models import Prefetch

logger = logging.getLogger(__name__)

def generer_structure_donnees(user):
    try:
        # 1. Structure pour les machines et leurs tâches
        machines_structure = {}

        # Récupère les tâches de l'utilisateur uniquement
        taches_user = Tache.objects.filter(produit__user=user)

        # Extraction des machines
        machines_brutes = taches_user.values_list('machine', flat=True)
        liste_machines = []

        for machines in machines_brutes:
            for machine in machines.split(','):
                m = machine.strip()
                if m:
                    liste_machines.append(m)

        # Suppression des doublons et tri
        machines_distinctes = sorted(set(liste_machines))

        # Association machine → liste d'id_tache
        for machine in machines_distinctes:
            # Filtrer les tâches où le champ `machine` contient ce nom
            taches_machine = taches_user.filter(machine__icontains=machine).values_list('id_tache', flat=True)
            machines_structure[machine] = list(taches_machine)


        # 2. Structure pour les opérateurs (ici, tous les opérateurs — ou filtrer si liés à l’utilisateur)
        operateurs_structure = {}
        operateurs = Operateur.objects.prefetch_related(
            Prefetch('performanceoperateur_set',
                     queryset=PerformanceOperateur.objects.select_related('tache', 'tache__produit').filter(tache__produit__user=user))
        )

        for operateur in operateurs:
            performances = {
                perf.tache.id_tache: perf.performance_initiale / 100
                for perf in operateur.performanceoperateur_set.all()
            }

            operateurs_structure[operateur.id_operateur] = {
                "LC": float(operateur.lc) / 100,
                "FC": float(operateur.fc) / 100,
                "Performance": performances
            }

        # 3. Structure pour les produits de l'utilisateur
        produits_structure = []
        produits = Produit.objects.filter(user=user).prefetch_related('taches')

        for produit in produits:
            taches_produit = produit.taches.all()
            if taches_produit:
                taches_liste = []
                temps_standard_dict = {}
                machines_dict = {}

                for tache in taches_produit:
                    taches_liste.append(tache.id_tache)
                    temps_standard_dict[tache.id_tache] = float(tache.temps_standard)
                    machines_dict[tache.id_tache] = tache.machine

                try:
                    cr_value = float(produit.cr)
                except (TypeError, ValueError):
                    cr_value = 0.0

                produits_structure.append({
                    "ID": produit.id_produit,
                    "Tâches": taches_liste,
                    "Temps_standard": temps_standard_dict,
                    "Quantité": int(produit.quantite),
                    "Cr": cr_value,
                    "Machines": machines_dict
                })

        # 4. Structure des précédences
        precedences = {}
        produits_precedences = Produit.objects.filter(user=user).prefetch_related(
            Prefetch('taches', queryset=Tache.objects.order_by('ordre'))
        )

        for produit in produits_precedences:
            taches = list(produit.taches.all())
            if taches:
                for i in range(len(taches) - 1):
                    key = f'precedence{i + 1}'
                    if key not in precedences:
                        precedences[key] = {}
                    precedences[key][taches[i].id_tache] = taches[i + 1].id_tache

        precedences_list = [p for p in precedences.values()]
        return machines_structure, operateurs_structure, produits_structure, precedences_list

    except Exception as e:
        logger.error(f"Erreur dans generer_structure_donnees: {str(e)}", exc_info=True)
        raise

def default_example() :
    machines = {
        "M1": ['T111', 'T211', 'T331', 'T431', 'T511', 'T611', 'T731', 'T821'],
        "M2": ['T132', 'T322', 'T442', 'T522', 'T632', 'T832'],
        "M3": ['T123', 'T223', 'T313', 'T423', 'T533', 'T623', 'T713'],
        "M4": ['T144', 'T234', 'T414', 'T724', 'T814'],
        "M5": ['T245', 'T455', 'T545']
    }
    operateurs_data = {
            "O1": {
                "LC": 0.8, "FC": 0.45, "Md": 5, "Sd": 1440,
                "Performance": {
                    'T111': 0.3, 'T123': 0.7, 'T132': 0.6, 'T144': 0.5,
                    'T211': 0.35, 'T223': 0.5, 'T234': 0.35, 'T245': 0.4,
                    'T313': 0.75, 'T322': 0.48, 'T331': 0.58,
                    'T414': 0.3, 'T423': 0.4, 'T431': 0.6, 'T442': 0.45, 'T455': 0.35,
                    'T511': 0.25, 'T522': 0.6, 'T533': 0.7, 'T545': 0.4,
                    'T611': 0.2, 'T623': 0.4, 'T632': 0.5,
                    'T713': 0.7, 'T724': 0.7, 'T731': 0.2,
                    'T814': 0.4, 'T821': 0.6, 'T832': 0.7
                }
            },
            "O2": {
                "LC": 0.78, "FC": 0.12, "Md": 8, "Sd": 2880,
                "Performance": {
                    'T111': 0.51, 'T123': 0.58, 'T132': 0.5, 'T144': 0.55,
                    'T211': 0.6, 'T223': 0.6, 'T234': 0.25, 'T245': 0.3,
                    'T313': 0.45, 'T322': 0.38, 'T331': 0.31,
                    'T414': 0.6, 'T423': 0.22, 'T431': 0.58, 'T442': 0.35, 'T455': 0.25,
                    'T511': 0.6, 'T522': 0.5, 'T533': 0.68, 'T545': 0.45,
                    'T611': 0.27, 'T623': 0.26, 'T632': 0.25,
                    'T713': 0.58, 'T724': 0.26, 'T731': 0.37,
                    'T814': 0.5, 'T821': 0.8, 'T832': 0.9
                }
            },
            "O3": {
                "LC": 0.9, "FC": 0.35, "Md": 3, "Sd": 4320,
                "Performance": {
                    'T111': 0.6, 'T123': 0.5, 'T132': 0.7, 'T144': 0.6,
                    'T211': 0.2, 'T223': 0.5, 'T234': 1.0, 'T245': 0.8,
                    'T313': 0.45, 'T322': 0.92, 'T331': 0.87,
                    'T414': 1.0, 'T423': 0.2, 'T431': 0.9, 'T442': 0.7, 'T455': 0.6,
                    'T511': 0.2, 'T522': 0.58, 'T533': 0.6, 'T545': 0.5,
                    'T611': 0.55, 'T623': 0.27, 'T632': 0.68,
                    'T713': 0.9, 'T724': 0.5, 'T731': 0.26,
                    'T814': 0.7, 'T821': 0.5, 'T832': 0.4
                }
            },
            "O4": {
                "LC": 0.75, "FC": 0.22, "Md": 8, "Sd": 2880,
                "Performance": {
                    'T111': 0.27, 'T123': 0.97, 'T132': 0.85, 'T144': 0.75,
                    'T211': 0.94, 'T223': 0.75, 'T234': 0.28, 'T245': 0.35,
                    'T313': 0.55, 'T322': 0.29, 'T331': 0.37,
                    'T414': 0.75, 'T423': 0.69, 'T431': 0.79, 'T442': 0.65, 'T455': 0.45,
                    'T511': 0.38, 'T522': 0.9, 'T533': 0.85, 'T545': 0.6,
                    'T611': 0.65, 'T623': 0.8, 'T632': 0.39,
                    'T713': 0.75, 'T724': 0.28, 'T731': 0.9,
                    'T814': 0.65, 'T821': 0.25, 'T832': 0.2
                }
            }
        }
    produits_data = [
        {
            "ID": "P1", 
            "Tâches": ["T111", "T132", "T123", "T144"], 
            "Temps_standard": {"T111": 10, "T132": 15, "T123": 15, "T144": 15}, 
            "Quantité": 21, 
            "Cr": 15,
            "Machines": {"T111": "M1", "T132": "M2", "T123": "M3", "T144": "M4"}
        },
        {
            "ID": "P2", 
            "Tâches": ["T211", "T223", "T234", "T245"], 
            "Temps_standard": {"T211": 25, "T223": 10, "T234": 15, "T245": 5}, 
            "Quantité": 10, 
            "Cr": 16,
            "Machines": {"T211": "M1", "T223": "M3", "T234": "M4", "T245": "M5"}
        },
        {
            "ID": "P3", 
            "Tâches": ["T313", "T322", "T331"], 
            "Temps_standard": {"T313": 5, "T322": 10, "T331": 15}, 
            "Quantité": 20, 
            "Cr": 27.5,
            "Machines": {"T313": "M3", "T322": "M2", "T331": "M1"}
        },
        {
            "ID": "P4", 
            "Tâches": ["T414", "T423", "T431", "T442", "T455"], 
            "Temps_standard": {"T414": 20, "T423": 15, "T431": 10, "T442": 10, "T455": 5}, 
            "Quantité": 10, 
            "Cr": 18,
            "Machines": {"T414": "M4", "T423": "M3", "T431": "M1", "T442": "M2", "T455": "M5"}
        },
        {
            "ID": "P5", 
            "Tâches": ["T511", "T522", "T533", "T545"], 
            "Temps_standard": {"T511": 10, "T522": 15, "T533": 20, "T545": 5}, 
            "Quantité": 15, 
            "Cr": 16,
            "Machines": {"T511": "M1", "T522": "M2", "T533": "M3", "T545": "M5"}
        },
        {
            "ID": "P6", 
            "Tâches": ["T611", "T623", "T632"], 
            "Temps_standard": {"T611": 15, "T623": 15, "T632": 30}, 
            "Quantité": 25, 
            "Cr": 25,
            "Machines": {"T611": "M1", "T623": "M3", "T632": "M2"}
        },
        {
            "ID": "P7", 
            "Tâches": ["T713", "T724", "T731"], 
            "Temps_standard": {"T713": 30, "T724": 25, "T731": 15}, 
            "Quantité": 25, 
            "Cr": 25,
            "Machines": {"T713": "M3", "T724": "M4", "T731": "M1"}
        },
        {
            "ID": "P8", 
            "Tâches": ["T814", "T821", "T832"], 
            "Temps_standard": {"T814": 20, "T821": 10, "T832": 15}, 
            "Quantité": 20, 
            "Cr": 27,
            "Machines": {"T814": "M4", "T821": "M1", "T832": "M2"}
        } ] 
        # Liste des précédences pour les produits avec 3 tâches
    precedance1 = {
    # P1: T111 -> T123 -> T132 -> T144
    'T111': 'T123',
    
    # P2: T211 -> T223 -> T234 -> T245
    'T211': 'T223',
    
    # P3: T313 -> T322 -> T331
    'T313': 'T322',
    
    # P4: T414 -> T423 -> T431 -> T442 -> T455
    'T414': 'T423',
    
    # P5: T511 -> T522 -> T533 -> T545
    'T511': 'T522',
    
    # P6: T611 -> T623 -> T632
    'T611': 'T623',
    
    # P7: T713 -> T724 -> T731
    'T713': 'T724',
    
    # P8: T814 -> T821 -> T832
    'T814': 'T821'
}
    precedance2 = {
        # P1
        'T123': 'T132',
        
        # P2
        'T223': 'T234',
        
        # P3
        'T322': 'T331',
        
        # P4
        'T423': 'T431',
        
        # P5
        'T522': 'T533',
        
        # P6
        'T623': 'T632',
        
        # P7
        'T724': 'T731',
        
        # P8
        'T821': 'T832'
    }
    precedance3 = {
        # P1: 3ème -> 4ème tâche
        'T132': 'T144',
        
        # P2: 3ème -> 4ème tâche
        'T234': 'T245',
        
        # P4: 3ème -> 4ème tâche
        'T431': 'T442',
        
        # P5: 3ème -> 4ème tâche
        'T533': 'T545'
    }
    precedance4 = {
        # P4: 4ème -> 5ème tâche
        'T442': 'T455'
    }
    precedence=[precedance1, precedance2, precedance3, precedance4]
    return machines, operateurs_data, produits_data, precedence

def initialiser_systeme(validation,poids,user):
    """Initialise toutes les structures de données à partir des données fournies"""
    if validation==1:
        machines_data, operateurs_data, produits_data, preced=generer_structure_donnees(user)
    else:
        machines_data, operateurs_data, produits_data, preced=default_example()
    # 1. Création des machines
    Machine.instances = []
    machines = [Machine(machine_id, list_taches) for machine_id, list_taches in machines_data.items()]
    
    # 2. Création des opérateurs
    Operator.instances=[]
    operateurs = []
    for op_id, op_data in operateurs_data.items():
        operateurs.append(Operator(
            op_id=op_id,
            learning_params={"LC": op_data["LC"], "FC": op_data["FC"]},
            initial_performance=dict(op_data["Performance"])  # ✅ ici
        ))
    
    # 3. Création des produits et tâches
    produits = []
    taches_initiales=[]
    Product.instances=[]
    Task.instances=[]
    taches = {}
    for prod_data in produits_data:
        # Création du produit
        machines_requises = {}
        for tache_id in prod_data["Tâches"]:
            # Trouver la machine compatible
            machines_compatibles=[]
            for machine in machines:
                if tache_id in machine.taches_compatibles:
                    machines_compatibles.append(machine)
                    machines_requises[tache_id] = machines_compatibles
                    
        product = Product(
            pid=prod_data["ID"],
            tasks=prod_data["Tâches"],
            std_times=prod_data["Temps_standard"],
            quantity=prod_data["Quantité"],
            cr=prod_data["Cr"],
            machines_requises=machines_requises
        )
        produits.append(product)
        
        # Création des tâches avec précédences
        for tache_id in prod_data["Tâches"]:
            precedence = None
            for precedance in preced:
                if tache_id in precedance.values():
                    # Trouver la valeure qui a cette tâche comme clee
                    for k, v in precedance.items():
                        if v == tache_id:
                            precedence = k
                            break

            task = Task(
                tid=tache_id,
                product=product,
                phase=prod_data["Tâches"].index(tache_id)+1,
                precedence=precedence
            )
            taches[tache_id] = task
    for task in Task.instances:
        if task.precedence:
            for tasksecond in Task.instances:
                if task.precedence == tasksecond.id:
                    task.precedence=tasksecond   
        else:
            taches_initiales.append(task.id)
    # 4. Initialisation des autres composants
    Simulation.instances=[]
    simulation = Simulation()
    ordonnanceur = Ordonnanceur(
        poids_cout=poids['poids_cout'],
        poids_equite=poids['poids_equite'],
        poids_makespan=poids['poids_makespan'],
        poids_performance=poids['poids_performance'],
        poids_penalite_attente=poids['poids_penalite_attente']
    )
    cout_global = Cout()

    return produits, operateurs, machines, simulation, ordonnanceur, cout_global,taches_initiales

def demarrer_simulation(validation,poids, user):
    """Lance la simulation principale avec gestion optimisée des affectations initiales"""
    produits, operateurs, machines, simulation, ordonnanceur, cout_global,taches_initiales = initialiser_systeme(validation,poids,user)
    # 1. Préparation des structures de données
    taches_affectees = set()
    operateurs_disponibles = operateurs
    # 2. Tri des opérateurs par performance globale décroissante
    operateurs = sorted(operateurs_disponibles, 
                            key=lambda op: sum(op.performancess.values()), 
                            reverse=True)
    print(list(op.id for op in operateurs))
    # 3. Affectation initiale optimisée
    for op in operateurs:
        meilleure_tache = None
        meilleur_score = -1
        
        # Recherche de la meilleure tâche initiale pour cet opérateur
        for tache_id in taches_initiales:
            if tache_id in taches_affectees:
                continue
                
            if tache_id in op.performancess  and op.performancess[tache_id] >= 0.35:
                tache = next(t for t in Task.instances if t.id == tache_id)
                
                # Vérification des contraintes
                if (tache.product.quantite_restante > 0 and 
                    tache.machine_requise.tache_actuelle is None):
                    
                    # Calcul du score basé sur la performance et le coût
                    temps_estime = tache.temps_standard / op.performancess  [tache_id]
                    cout_estime = (temps_estime - tache.temps_standard) * tache.product.cr
                    score = op.performancess[tache_id] / (cout_estime + 1e-6)  # Éviter division par zéro
                    
                    if score > meilleur_score:
                        meilleur_score = score
                        meilleure_tache = tache
        # Affectation si une tâche valide a été trouvée
        if meilleure_tache:
            quantite = meilleure_tache.quantite
            temps_unitaire = meilleure_tache.temps_standard + meilleure_tache.temps_standard*(1-op.performancess  [meilleure_tache.id])
            temps_reel = temps_unitaire * quantite
            # Création des événements
            temps_debut=simulation.temps_actuel+meilleure_tache.temps_attente
            temps_fin=temps_debut+temps_reel
            debut_event = Evenement(
                temps=temps_debut,
                type="DEBUT_TACHE",
                tache=meilleure_tache,
                operateur=op,
                machine=meilleure_tache.machine_requise
            )
            
            fin_event = Evenement(
                temps=temps_fin,
                type="FIN_TACHE",
                tache=meilleure_tache,
                operateur=op,
                machine=meilleure_tache.machine_requise
            )
            # Enregistrement des événements
            simulation.ajouter_evenement(debut_event)
            simulation.ajouter_evenement(fin_event)
            # Mise à jour des états
            taches_affectees.add(meilleure_tache.id)
            op.tache_actuellee= meilleure_tache
            meilleure_tache.operateur_affecte = op
            meilleure_tache.temps_debut = temps_debut
            meilleure_tache.quantite_restante = 0
            meilleure_tache.temps_fin = temps_fin

            op.mettre_a_jour_performance(meilleure_tache.id,temps_fin,simulation)

            machine = meilleure_tache.machine_requise 
            machine.historique.append((meilleure_tache.id,op.id,temps_debut,temps_fin))
            machine.tache_actuelle=tache
            op.machine_actuelle=machine.id
            op.historique_travail.append((meilleure_tache.id,temps_debut,temps_fin))
            
            #print('historique des taches',op.historique_travail )
            print(f"Affectation initiale: {op.id} → {meilleure_tache.id} "
                  f"(Performance: {op.performancess [meilleure_tache.id]:.2f}, "
                  f"Temps estimé: {temps_reel:.1f} min quantite: {meilleure_tache.quantite})")
        else:
            # Chercher une nouvelle tâche pour l'opérateur
            tache_suivante = ordonnanceur.choisir_tache(
                operateur=op,
                simulation=simulation,
                tache_finie=None
            )
    
            if tache_suivante:
                success = ordonnanceur.affecter_tache(
                    operateur=op,
                    tache=tache_suivante,
                    simulation=simulation
                )
                if not success:
                    print(f"Échec d'affectation pour {op.id}")
    
    # 4. Vérification des affectations
    if not taches_affectees:
        print("Avertissement: Aucune tâche initiale n'a pu être affectée!")
        return
    # 5. Lancement de la boucle principale
    boucle_principale(simulation, ordonnanceur,cout_global)
    return get_data(operateurs,simulation,cout_global)


