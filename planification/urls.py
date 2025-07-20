from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('produits/', views.saisie_produits, name='saisie_produits'),
    path('taches/', views.saisie_taches, name='saisie_taches'),
    path('produits/<int:produit_id>/taches/', views.saisie_taches, name='saisie_taches'),
    path('produits/<int:produit_id>/', views.saisie_produits, name='saisie_produits'),
    path('operateurs/', views.saisie_operateurs, name='saisie_operateurs'),
    path('config-poids/', views.config_poids, name='config_poids'),
    path('simulation/exemple/', views.exemple_simulation, name='exemple_simulation'),
    path('', views.home, name='home'),
    path('exemple-detaille/', views.exemple_detaille, name='exemple_detaille'),
    path('produit/<int:produit_id>/supprimer/', views.supprimer_produit, name='supprimer_produit'),
    path('tache/<int:tache_id>/supprimer/', views.supprimer_tache, name='supprimer_tache'),
    path('apercu/produit/<int:produit_id>/supprimer/', views.supprimer_produit_apercu, name='supprimer_produit_apercu'),
    path('apercu/tache/<int:tache_id>/supprimer/', views.supprimer_tache_apercu, name='supprimer_tache_apercu'),
    path('produit/<int:produit_id>/modifier/', views.modifier_produit, name='modifier_produit'),
    path('tache/<int:tache_id>/modifier/', views.modifier_tache, name='modifier_tache'),
    path('apercu_donnees/', views.apercu_donnees, name='apercu_donnees'),
    path('operateur/<int:operateur_id>/modifier/', views.modifier_operateur, name='modifier_operateur'),
    path('operateur/<int:operateur_id>/supprimer/', views.supprimer_operateur, name='supprimer_operateur'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html',next_page='login', http_method_names=['get', 'post']), name='logout'),
]