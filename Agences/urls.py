from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),
    path('profil/modifier/', views.modifier_profil_view, name='modifier_profil'),
    path('profil/changer-password/', views.changer_password_view, name='changer_password'),
    path('agences/', views.agences_view, name='agences'),
    path('commercial/', views.interface_commercial, name='interface_commercial'),
    #path('ca/', views.interface_ca, name='interface_ca'),
    path('prod/', views.interface_prod, name='interface_prod'),
    path('api/get-responsables-ca/', views.get_responsables_ca, name='get_responsables_ca'),

    # ... APPEL OFFRE ...
    path('api/appels-offre/', views.get_appels_offre_json, name='get_appels_offre_json'),
    path('api/appels-offre/create/', views.create_appel_offre, name='create_appel_offre'),
    path('api/appels-offre/<int:appel_id>/statut/', views.update_appel_offre_statut, name='update_appel_offre_statut'),
    path('api/appels-offre/retard/', views.get_appels_en_retard, name='get_appels_en_retard'),

    # ... COULEUR OFFRE ...
    path('api/agences-couleurs/', views.get_agences_couleurs, name='get_agences_couleurs'),


    # ... CA ...
    path('interface-ca/', views.interface_ca, name='interface_ca'),
    path('api/projets-ca/', views.get_projets_ca, name='get_projets_ca'),
    path('api/agences-couleurs/', views.get_agences_couleurs_ca, name='get_agences_couleurs_ca'),
    path('api/responsables-prod/', views.get_responsables_prod, name='get_responsables_prod'),
    path('api/commencer-terrain-france/', views.commencer_terrain_france, name='commencer_terrain_france'),
    path('api/fin-terrain-france/<int:projet_id>/', views.fin_terrain_france, name='fin_terrain_france'),
    path('api/commencer-traitement-france/', views.commencer_traitement_france, name='commencer_traitement_france'),
    path('api/fin-traitement-france/<int:projet_id>/', views.fin_traitement_france, name='fin_traitement_france'),
    path('api/envoyer-donnees-mada/', views.envoyer_donnees_mada, name='envoyer_donnees_mada'),
    path('api/projets-retard-ca/', views.get_projets_en_retard_ca, name='get_projets_en_retard_ca'),


    # ... PROD ...
    path('api/projets-prod/', views.get_projets_prod, name='get_projets_prod'),
    path('api/responsables-ca/', views.get_responsables_ca, name='get_responsables_ca'),
    path('api/reception-donnees/<int:projet_id>/', views.reception_donnees, name='reception_donnees'),
    path('api/envoie-reprise/<int:projet_id>/', views.envoie_reprise, name='envoie_reprise'),
    path('api/commencer-prod-mada/', views.commencer_prod_mada, name='commencer_prod_mada'),
    path('api/fin-prod-mada/<int:projet_id>/', views.fin_prod_mada, name='fin_prod_mada'),
    path('api/gestion-complement/<int:projet_id>/', views.gestion_complement, name='gestion_complement'),

    # ... Confirmation du problème ...
    path('api/confirmer-probleme-reception/<int:projet_id>/', views.confirmer_probleme_reception, name='confirmer_probleme_reception'),

    # ... Envoie Reprise ...
]