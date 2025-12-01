from datetime import date, datetime

from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomUserCreationForm, LoginForm, CustomUserChangeForm
from .models import User, Agence, Poste, TypePrestation, AppelOffre
from django.db import models
import json


def home_view(request):
    """Vue pour la page d'accueil"""
    if request.user.is_authenticated:
        # Rediriger vers l'interface appropriée selon le poste
        if request.user.poste:
            if request.user.poste.nom == 'COMMERCIAL':
                return redirect('interface_commercial')
            elif request.user.poste.nom == 'CA':
                return redirect('interface_ca')
            elif request.user.poste.nom == 'PROD':
                return redirect('interface_prod')
        return redirect('profil')
    else:
        return redirect('login')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.prenoms} !')
                # Redirection selon le poste
                if user.poste:
                    if user.poste.nom == 'COMMERCIAL':
                        return redirect('interface_commercial')
                    elif user.poste.nom == 'CA':
                        return redirect('interface_ca')
                    elif user.poste.nom == 'PROD':
                        return redirect('interface_prod')
                return redirect('profil')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = LoginForm()

    return render(request, 'Agences/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Compte créé avec succès!')
            return redirect('profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomUserCreationForm()

    # Récupérer les données pour les listes déroulantes
    agences = Agence.objects.all()
    postes = Poste.objects.all()
    prestations = TypePrestation.objects.all()

    return render(request, 'Agences/register.html', {
        'form': form,
        'agences': agences,
        'postes': postes,
        'prestations': prestations
    })


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('login')


@login_required
def profil_view(request):
    return render(request, 'Agences/profil.html')


@login_required
def modifier_profil_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomUserChangeForm(instance=request.user)

    agences = Agence.objects.all()
    postes = Poste.objects.all()
    prestations = TypePrestation.objects.all()

    return render(request, 'Agences/modifier_profil.html', {
        'form': form,
        'agences': agences,
        'postes': postes,
        'prestations': prestations
    })


@login_required
def changer_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important pour ne pas déconnecter l'utilisateur
            messages.success(request, 'Votre mot de passe a été changé avec succès!')
            return redirect('profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'Agences/changer_password.html', {'form': form})


@login_required
def agences_view(request):
    # Récupérer toutes les agences
    agences = Agence.objects.all()

    # Préparer les données pour chaque agence
    agences_avec_membres = []
    total_membres_meme_poste = 0
    repartition_poste = {}

    for agence in agences:
        # Récupérer tous les membres de l'agence
        membres_agence = agence.user_set.all()

        # Filtrer par poste de l'utilisateur connecté
        if request.user.poste:
            membres_meme_poste = membres_agence.filter(poste=request.user.poste)
        else:
            membres_meme_poste = membres_agence.none()

        # Compter les membres du même poste
        membres_meme_poste_count = membres_meme_poste.count()
        total_membres_meme_poste += membres_meme_poste_count

        # Récupérer la liste des membres du même poste (limité à 10 pour l'affichage)
        membres_meme_poste_list = membres_meme_poste[:10]

        # Statistiques de répartition par poste pour cette agence
        postes_agence = {}
        for poste in Poste.objects.all():
            count = membres_agence.filter(poste=poste).count()
            if count > 0:
                postes_agence[poste.get_nom_display()] = count

        repartition_poste[agence.nom] = postes_agence

        # Ajouter l'agence avec ses données
        agences_avec_membres.append({
            'agence': agence,
            'membres_count': membres_agence.count(),
            'membres_meme_poste_count': membres_meme_poste_count,
            'membres_meme_poste': membres_meme_poste_list,
            'date_creation': agence.date_creation,
            'created_by': agence.created_by
        })

    # Trouver l'agence avec le plus de membres du même poste
    agence_plus_membres = None
    max_membres = 0
    for agence_data in agences_avec_membres:
        if agence_data['membres_meme_poste_count'] > max_membres:
            max_membres = agence_data['membres_meme_poste_count']
            agence_plus_membres = agence_data['agence']

    # Calculer la moyenne des membres du même poste par agence
    moyenne_membres_meme_poste = total_membres_meme_poste / len(agences) if agences else 0

    context = {
        'agences': agences_avec_membres,
        'total_agences': len(agences),
        'total_membres': User.objects.count(),
        'total_membres_meme_poste': total_membres_meme_poste,
        'moyenne_membres': User.objects.count() / len(agences) if agences else 0,
        'moyenne_membres_meme_poste': moyenne_membres_meme_poste,
        'derniere_agence': agences.order_by('-date_creation').first(),
        'agence_plus_membres': agence_plus_membres,
        'repartition_poste': repartition_poste,
    }

    return render(request, 'Agences/agences.html', context)


##############################################
#############Commerciale######################
##############################################

@login_required
def interface_commercial(request):
    if not request.user.poste or request.user.poste.nom != 'COMMERCIAL':
        messages.error(request, "Vous n'avez pas accès à cette interface.")
        return redirect('profil')

    # Récupérer les données pour le formulaire
    agences = Agence.objects.all()
    prestations = TypePrestation.objects.all()

    # Récupérer les appels d'offre de l'utilisateur connecté
    appels_offre = AppelOffre.objects.filter(commercial=request.user).select_related(
        'agence', 'responsable_ca', 'commercial'
    ).prefetch_related('prestations')

    # Mettre à jour les statuts automatiquement
    update_appels_statuts(appels_offre)

    return render(request, 'Agences/interfaces/commercial.html', {
        'agences': agences,
        'prestations': prestations,
        'appels_offre': appels_offre
    })


def update_appels_statuts(appels_offre):
    """Met à jour les statuts des appels d'offre automatiquement"""
    today = date.today()

    for appel in appels_offre:
        if appel.statut in ['gagne', 'perdu']:
            continue

        if today >= appel.date_debut and appel.statut == 'en_attente':
            appel.statut = 'en_cours'
            appel.save()
        elif today > appel.date_fin and appel.statut == 'en_cours' and not appel.date_fin_reelle:
            # Appel en retard - on pourrait notifier ici
            pass


@csrf_exempt
@login_required
def create_appel_offre(request):
    """Crée un nouvel appel d'offre"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validation des dates
            date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
            date_fin = datetime.strptime(data['date_fin'], '%Y-%m-%d').date()

            if date_debut >= date_fin:
                return JsonResponse({'error': 'La date de fin doit être postérieure à la date de début'}, status=400)

            # Génération de la référence
            last_ao = AppelOffre.objects.filter(
                created_at__year=date.today().year
            ).order_by('-id').first()

            next_number = 1
            if last_ao:
                try:
                    last_number = int(last_ao.reference.split('-')[-1])
                    next_number = last_number + 1
                except:
                    next_number = 1

            reference = f"AO-{date.today().year}-{str(next_number).zfill(3)}"

            # Création de l'appel d'offre
            appel_offre = AppelOffre.objects.create(
                reference=reference,
                agence_id=data['agence_id'],
                date_debut=date_debut,
                date_fin=date_fin,
                responsable_ca_id=data['responsable_ca_id'],
                commercial=request.user,
                description=data.get('description', ''),
                couleur=data.get('couleur', '#007bff')
            )

            # Ajout des prestations
            prestations_ids = data.get('prestations_ids', [])
            appel_offre.prestations.set(prestations_ids)

            return JsonResponse({
                'success': True,
                'appel_offre': {
                    'id': appel_offre.id,
                    'reference': appel_offre.reference,
                    'agence': appel_offre.agence.nom,
                    'date_debut': appel_offre.date_debut.isoformat(),
                    'date_fin': appel_offre.date_fin.isoformat(),
                    'statut': appel_offre.get_statut_display(),
                    'couleur': appel_offre.couleur
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def update_appel_offre_statut(request, appel_id):
    """Met à jour le statut d'un appel d'offre"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nouveau_statut = data['statut']
            commentaire = data.get('commentaire', '')

            appel_offre = AppelOffre.objects.get(id=appel_id, commercial=request.user)

            # Validation du changement de statut
            if appel_offre.statut in ['gagne', 'perdu']:
                return JsonResponse({'error': 'Impossible de modifier un appel terminé'}, status=400)

            appel_offre.statut = nouveau_statut
            appel_offre.date_fin_reelle = date.today()
            appel_offre.commentaire_arret = commentaire
            appel_offre.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Appel d\'offre non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def get_appels_offre_json(request):
    """Retourne les appels d'offre au format JSON pour le frontend"""
    appels_offre = AppelOffre.objects.filter(commercial=request.user).select_related(
        'agence', 'responsable_ca'
    ).prefetch_related('prestations')

    appels_data = []
    for appel in appels_offre:
        appels_data.append({
            'id': appel.id,
            'reference': appel.reference,
            'agence': appel.agence.nom,
            'prestations': [p.nom for p in appel.prestations.all()],
            'date_debut': appel.date_debut.isoformat(),
            'date_fin': appel.date_fin.isoformat(),
            'date_fin_reelle': appel.date_fin_reelle.isoformat() if appel.date_fin_reelle else None,
            'responsable': f"{appel.responsable_ca.prenoms} {appel.responsable_ca.nom}",
            'statut': appel.get_statut_display(),
            'description': appel.description,
            'commentaire_arret': appel.commentaire_arret,
            'couleur': appel.couleur,
            'created': appel.created_at.isoformat()
        })

    return JsonResponse({'appels_offre': appels_data})


@login_required
def get_appels_en_retard(request):
    """Retourne les appels d'offre en retard"""
    today = date.today()
    appels_retard = AppelOffre.objects.filter(
        commercial=request.user,
        statut='en_cours',
        date_fin__lt=today,
        date_fin_reelle__isnull=True
    )

    appels_data = []
    for appel in appels_retard:
        jours_retard = (today - appel.date_fin).days
        appels_data.append({
            'reference': appel.reference,
            'agence': appel.agence.nom,
            'jours_retard': jours_retard
        })

    return JsonResponse({'appels_retard': appels_data})


@login_required
def get_agences_couleurs(request):
    """Retourne les couleurs des agences depuis la base de données"""
    agences = Agence.objects.all().values('nom', 'couleur')
    couleurs = {agence['nom']: agence['couleur'] for agence in agences}
    return JsonResponse({'couleurs': couleurs})


##############################################
##############Chargé d' Affaire###############
##############################################

@login_required
def interface_ca(request):
    if not request.user.poste or request.user.poste.nom != 'CA':
        messages.error(request, "Vous n'avez pas accès à cette interface.")
        return redirect('profil')

    # Récupérer les agences pour les filtres
    agences = Agence.objects.all()

    return render(request, 'Agences/interfaces/ca.html', {
        'agences': agences
    })


@login_required
def get_projets_ca(request):
    """Retourne tous les projets pour l'interface CA avec TOUTES les données de l'AO original"""
    try:
        # Récupérer les appels d'offre gagnés qui sont devenus des projets CA
        projets = AppelOffre.objects.filter(
            statut='gagne'
        ).select_related('agence', 'responsable_ca', 'commercial', 'agence_terrain', 'agence_traitement',
                         'responsable_prod_terrain', 'responsable_prod_traitement').prefetch_related('prestations')

        projets_data = []
        for projet in projets:
            # Utiliser la méthode du modèle pour déterminer l'étape
            etape = get_etape_projet(projet)

            # Déterminer le responsable prod selon l'étape avec vérification
            responsable_prod_display = 'Non assigné'
            responsable_prod_terrain_display = 'Non assigné'
            responsable_prod_traitement_display = 'Non assigné'

            # Afficher les responsables selon leur assignation
            if projet.responsable_prod_terrain:
                responsable_prod_terrain_display = f"{projet.responsable_prod_terrain.prenoms} {projet.responsable_prod_terrain.nom}"
            if projet.responsable_prod_traitement:
                responsable_prod_traitement_display = f"{projet.responsable_prod_traitement.prenoms} {projet.responsable_prod_traitement.nom}"

            # Déterminer le responsable à afficher selon l'étape
            if etape in ['AO Gagné', 'Terrain France', 'Terrain France terminé']:
                responsable_prod_display = responsable_prod_terrain_display
            elif etape in ['Traitement France', 'Prêt pour envoi Mada']:
                responsable_prod_display = responsable_prod_traitement_display or responsable_prod_terrain_display
            else:
                responsable_prod_display = responsable_prod_traitement_display or responsable_prod_terrain_display

            # Récupérer les prestations originales
            prestations = [prestation.nom for prestation in projet.prestations.all()]

            projets_data.append({
                'id': projet.id,
                'reference': projet.reference,
                'nom_affaire': projet.nom_affaire or projet.reference,
                'agence': projet.agence.nom,

                # AJOUT: Inclure le champ probleme_confirme
                'probleme_confirme': getattr(projet, 'probleme_confirme', False),

                # Période AO Gagné
                'date_debut_ao': projet.date_debut.isoformat() if projet.date_debut else None,
                'date_fin_ao': projet.date_fin.isoformat() if projet.date_fin else None,
                'date_fin_reelle_ao': projet.date_fin_reelle.isoformat() if projet.date_fin_reelle else None,

                # Période Terrain France (si existante)
                'date_debut_terrain': projet.date_debut_terrain.isoformat() if projet.date_debut_terrain else None,
                'date_fin_prevue_terrain': projet.date_fin_prevue_terrain.isoformat() if projet.date_fin_prevue_terrain else None,
                'date_fin_terrain_reelle': projet.date_fin_terrain_reelle.isoformat() if projet.date_fin_terrain_reelle else None,

                # Agence Terrain
                'agence_terrain': {
                    'id': projet.agence_terrain.id if projet.agence_terrain else None,
                    'nom': projet.agence_terrain.nom if projet.agence_terrain else None
                },

                # Période Traitement France (si existante)
                'date_debut_traitement': projet.date_debut_traitement.isoformat() if projet.date_debut_traitement else None,
                'date_fin_prevue_traitement': projet.date_fin_prevue_traitement.isoformat() if projet.date_fin_prevue_traitement else None,
                'date_fin_traitement_reelle': projet.date_fin_traitement_reelle.isoformat() if projet.date_fin_traitement_reelle else None,

                # Agence Traitement
                'agence_traitement': {
                    'id': projet.agence_traitement.id if projet.agence_traitement else None,
                    'nom': projet.agence_traitement.nom if projet.agence_traitement else None
                },

                # Envoi Mada
                'date_envoi_mada': projet.date_envoi_mada.isoformat() if projet.date_envoi_mada else None,
                'date_livraison_prevue_mada': projet.date_livraison_prevue_mada.isoformat() if projet.date_livraison_prevue_mada else None,
                'date_livraison_reelle_mada': projet.date_livraison_reelle_mada.isoformat() if projet.date_livraison_reelle_mada else None,
                'info_supplementaire_mada': projet.info_supplementaire_mada,

                'prestations': prestations,
                'description': projet.description,
                'commentaire_arret': projet.commentaire_arret,
                'commentaire_fin_terrain': projet.commentaire_fin_terrain,
                'commentaire_fin_traitement': projet.commentaire_fin_traitement,
                'commentaire_fin_reprise': projet.commentaire_fin_reprise,
                'commentaire_fin_prod_mada': projet.commentaire_fin_prod_mada,

                'historique_commentaires': getattr(projet, 'historique_commentaires', []),

                'responsable_prod': responsable_prod_display,
                'responsable_prod_terrain': responsable_prod_terrain_display,
                'responsable_prod_traitement': responsable_prod_traitement_display,
                'etape': etape,
                'couleur': projet.couleur,
                'commercial': f"{projet.commercial.prenoms} {projet.commercial.nom}",
                'responsable_ca': f"{projet.responsable_ca.prenoms} {projet.responsable_ca.nom}",
                'date_creation': projet.created_at.isoformat(),
            })

        return JsonResponse({'projets': projets_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_etape_projet(projet):
    """Détermine l'étape actuelle d'un projet"""
    if projet.statut != 'gagne':
        return 'Non gagné'

    # Récupérer les étapes avec getattr pour éviter les erreurs
    etape_terrain = getattr(projet, 'etape_terrain_france', 'en_attente')
    etape_traitement = getattr(projet, 'etape_traitement_france', 'en_attente')
    etape_envoi_mada = getattr(projet, 'etape_envoi_mada', 'en_attente')
    date_reception_france = getattr(projet, 'date_reception_france', None)
    etape_reprise = getattr(projet, 'etape_reprise_france', 'en_attente')
    etape_prod = getattr(projet, 'etape_prod_mada', 'en_attente')
    commentaire_fin_reprise = getattr(projet, 'commentaire_fin_reprise', '')
    probleme_confirme = getattr(projet, 'probleme_confirme', False)

    print(f"Debug CA {projet.reference}: envoi={etape_envoi_mada}, date_reception={date_reception_france}, probleme_confirme={probleme_confirme}")

    if etape_terrain == 'en_attente':
        return 'AO Gagné'
    elif etape_terrain == 'en_cours':
        return 'Terrain France'
    elif etape_terrain == 'termine' and etape_traitement == 'en_attente':
        return 'Traitement France'
    elif etape_traitement == 'en_cours':
        return 'Traitement France en cours'
    elif etape_traitement == 'termine' and etape_envoi_mada == 'en_attente':
        return 'Prêt pour envoi Mada'

    # CORRECTION : Logique simplifiée pour l'envoi Mada
    elif etape_envoi_mada == 'en_cours' and not date_reception_france:
        if commentaire_fin_reprise:
            return 'Problème de réception'  # Non reçu, prêt pour ré-envoi
        else:
            return 'Envoi des données à Mada'  # En cours d'envoi initial

    elif etape_envoi_mada == 'termine' and date_reception_france and etape_reprise in [None, 'en_attente']:
        return 'Reprise des données France'
    elif date_reception_france and etape_reprise in [None, 'en_attente']:
        return 'Reprise des données France'
    elif etape_reprise == 'en_cours':
        return 'Reprise des données France'
    elif etape_reprise == 'termine' and etape_prod in [None, 'en_attente']:
        return 'Prod en cours Mada'
    elif etape_prod == 'en_cours':
        return 'Prod en cours Mada'
    elif etape_prod == 'termine':
        return 'Production terminée'
    else:
        return 'En attente'


@login_required
def get_agences_couleurs_ca(request):
    """Retourne les couleurs des agences pour l'interface CA"""
    agences = Agence.objects.all().values('nom', 'couleur')
    couleurs = {agence['nom']: agence['couleur'] for agence in agences}
    return JsonResponse({'couleurs': couleurs})



@csrf_exempt
@login_required
def commencer_terrain_france(request):
    """Démarre la phase Terrain France pour un projet"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            projet_id = data['projet_id']

            # Récupérer l'appel d'offre/projet
            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Validation des dates
            date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
            date_fin_prevue = datetime.strptime(data['date_fin_prevue'], '%Y-%m-%d').date()

            if date_debut >= date_fin_prevue:
                return JsonResponse({'error': 'La date de fin doit être postérieure à la date de début'}, status=400)

            # CORRECTION : Utiliser le bon champ responsable_prod_terrain_id
            projet.nom_affaire = data['nom_affaire']
            projet.date_debut_terrain = date_debut
            projet.date_fin_prevue_terrain = date_fin_prevue
            projet.agence_terrain_id = data['agence_id']
            projet.responsable_prod_terrain_id = data['responsable_prod_id']  # CORRECTION ICI
            projet.etape_terrain_france = 'en_cours'
            projet.date_debut_terrain_reelle = date.today()
            projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def fin_terrain_france(request, projet_id):
    """Termine la phase Terrain France et passe à Traitement France"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commentaire = data.get('commentaire', '')

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Marquer le terrain France comme terminé et passer à Traitement France
            projet.etape_terrain_france = 'termine'
            projet.etape_traitement_france = 'en_attente'  # Nouvelle étape
            projet.date_fin_terrain_reelle = date.today()
            projet.commentaire_fin_terrain = commentaire
            projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def commencer_traitement_france(request):
    """Démarre la phase Traitement France"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            projet_id = data['projet_id']

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Validation des dates
            date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
            date_fin_prevue = datetime.strptime(data['date_fin_prevue'], '%Y-%m-%d').date()

            if date_debut >= date_fin_prevue:
                return JsonResponse({'error': 'La date de fin doit être postérieure à la date de début'}, status=400)

            # Mettre à jour pour le traitement France
            projet.nom_affaire_traitement = data['nom_affaire']
            projet.date_debut_traitement = date_debut
            projet.date_fin_prevue_traitement = date_fin_prevue
            projet.agence_traitement_id = data['agence_id']
            projet.responsable_prod_traitement_id = data['responsable_prod_id']  # Déjà correct
            projet.etape_traitement_france = 'en_cours'
            projet.date_debut_traitement_reelle = date.today()
            projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def fin_traitement_france(request, projet_id):
    """Termine la phase Traitement France et passe à Envoi Mada"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commentaire = data.get('commentaire', '')

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Marquer le traitement France comme terminé ET préparer Envoi Mada
            projet.etape_traitement_france = 'termine'
            projet.etape_envoi_mada = 'en_attente'  # ← AJOUT : Prépare la phase suivante
            projet.date_fin_traitement_reelle = date.today()
            projet.commentaire_fin_traitement = commentaire
            projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def envoyer_donnees_mada(request):
    """Envoie les données à Madagascar"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            projet_id = data['projet_id']

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Validation des dates
            date_envoi = datetime.strptime(data['date_envoi'], '%Y-%m-%d').date()
            date_livraison = datetime.strptime(data['date_livraison'], '%Y-%m-%d').date()

            if date_envoi >= date_livraison:
                return JsonResponse({'error': 'La date de livraison doit être postérieure à la date d\'envoi'},
                                    status=400)

            # SAUVEGARDER L'ANCIEN COMMENTAIRE DANS L'HISTORIQUE SI EXISTANT
            if projet.commentaire_fin_reprise and projet.commentaire_fin_reprise.strip():
                if not hasattr(projet, 'historique_commentaires'):
                    projet.historique_commentaires = []

                historique_entry = {
                    'date': date.today().isoformat(),
                    'commentaire': projet.commentaire_fin_reprise,
                    'type': 'avant_reenvoi',
                    'etape_envoi_mada': projet.etape_envoi_mada
                }
                projet.historique_commentaires.append(historique_entry)

            # Réinitialiser pour nouvel envoi
            projet.date_envoi_mada = date_envoi
            projet.date_livraison_prevue_mada = date_livraison
            projet.info_supplementaire_mada = data.get('info_supplementaire', '')
            projet.etape_envoi_mada = 'en_cours'
            projet.date_reception_france = None
            projet.etape_reprise_france = 'en_attente'
            projet.commentaire_fin_reprise = ''  # Vider pour nouvel envoi
            projet.probleme_confirme = False
            projet.save()

            print(f"Envoi Mada - Projet {projet.reference} : nouvel envoi, historique préservé")

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def get_projets_en_retard_ca(request):
    """Retourne les projets en retard pour l'interface CA"""
    today = date.today()

    projets_retard = AppelOffre.objects.filter(
        statut='gagne'
    ).select_related('agence')

    projets_retard_data = []

    for projet in projets_retard:
        retard = False
        jours_retard = 0

        # Vérifier selon l'étape
        if projet.etape_terrain_france == 'en_cours' and projet.date_fin_prevue_terrain and projet.date_fin_prevue_terrain < today:
            retard = True
            jours_retard = (today - projet.date_fin_prevue_terrain).days
        elif projet.etape_traitement_france == 'en_cours' and projet.date_fin_prevue_traitement and projet.date_fin_prevue_traitement < today:
            retard = True
            jours_retard = (today - projet.date_fin_prevue_traitement).days
        elif projet.etape_envoi_mada == 'en_cours' and projet.date_livraison_prevue_mada and projet.date_livraison_prevue_mada < today:
            retard = True
            jours_retard = (today - projet.date_livraison_prevue_mada).days

        if retard:
            projets_retard_data.append({
                'reference': projet.reference,
                'nom_affaire': getattr(projet, 'nom_affaire', projet.reference),
                'agence': projet.agence.nom,
                'etape': get_etape_projet(projet),
                'jours_retard': jours_retard
            })

    return JsonResponse({'projets_retard': projets_retard_data})



##############################################
#####################PROD#####################
##############################################

@login_required
def get_responsables_prod(request):
    """Retourne la liste des responsables production"""
    try:
        responsables = User.objects.filter(
            poste__nom='PROD'
        ).select_related('agence', 'poste')

        responsables_data = []
        for responsable in responsables:
            responsables_data.append({
                'id': responsable.id,
                'prenoms': responsable.prenoms,
                'nom': responsable.nom,
                'pseudo': responsable.pseudo,
                'agence': responsable.agence.nom if responsable.agence else 'Non assigné'
            })

        return JsonResponse({'responsables': responsables_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def interface_prod(request):
    if not request.user.poste or request.user.poste.nom != 'PROD':
        messages.error(request, "Vous n'avez pas accès à cette interface.")
        return redirect('profil')

    agences = Agence.objects.all()  # Pour filtres

    return render(request, 'Agences/interfaces/prod.html', {
        'agences': agences
    })


@csrf_exempt
def get_responsables_ca(request):
    if request.method == 'GET':
        try:
            # Récupérer les paramètres depuis l'URL
            agence_id = request.GET.get('agence_id')
            prestation_ids = request.GET.get('prestation_ids', '')

            # Convertir les IDs de prestations en liste
            prestation_ids_list = []
            if prestation_ids:
                prestation_ids_list = [int(pid) for pid in prestation_ids.split(',') if pid.isdigit()]

            # Filtrer les responsables CA
            responsables_query = User.objects.filter(
                poste__nom='CA'
            ).select_related('agence', 'poste').prefetch_related('types_prestation')

            # Appliquer les filtres si des paramètres sont fournis
            if agence_id and agence_id.isdigit():
                responsables_query = responsables_query.filter(agence_id=int(agence_id))

            if prestation_ids_list:
                responsables_query = responsables_query.filter(types_prestation__id__in=prestation_ids_list).distinct()

            responsables_data = []
            for responsable in responsables_query:
                prestations = [{
                    'id': p.id,
                    'nom': p.nom
                } for p in responsable.types_prestation.all()]

                responsables_data.append({
                    'id': responsable.id,
                    'prenoms': responsable.prenoms,
                    'nom': responsable.nom,
                    'pseudo': responsable.pseudo,
                    'agence': {
                        'id': responsable.agence.id if responsable.agence else None,
                        'nom': responsable.agence.nom if responsable.agence else 'Non assigné'
                    },
                    'poste': {
                        'nom': responsable.poste.get_nom_display() if responsable.poste else ''
                    },
                    'types_prestation': prestations
                })

            return JsonResponse({'responsables': responsables_data})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def get_projets_prod(request):
    """Retourne les projets pour l'interface PROD"""
    try:
        print("=== DEBUT get_projets_prod ===")

        # Récupérer tous les projets gagnés pour PROD
        projets = AppelOffre.objects.filter(
            statut='gagne'
        ).select_related('agence', 'responsable_ca', 'commercial').prefetch_related('prestations')

        print(f"Nombre de projets trouvés: {projets.count()}")

        projets_data = []
        for projet in projets:
            print(f"Traitement du projet: {projet.reference}")

            try:
                etape = get_etape_prod(projet)
                print(f"Étape déterminée: {etape}")

                projets_data.append({
                    'id': projet.id,
                    'reference': projet.reference,
                    'nom_affaire': getattr(projet, 'nom_affaire', projet.reference),
                    'agence': projet.agence.nom if projet.agence else 'Agence inconnue',
                    'date_envoi_mada': getattr(projet, 'date_envoi_mada', None),
                    'date_livraison_prevue_mada': getattr(projet, 'date_livraison_prevue_mada', None),
                    'info_supplementaire_mada': getattr(projet, 'info_supplementaire_mada', ''),
                    'commentaire_fin_reprise': getattr(projet, 'commentaire_fin_reprise', ''),
                    'date_reception_france': getattr(projet, 'date_reception_france', None),
                    'date_debut_reprise': getattr(projet, 'date_debut_reprise', None),
                    'date_fin_prevue_reprise': getattr(projet, 'date_fin_prevue_reprise', None),
                    'date_debut_prod_mada': getattr(projet, 'date_debut_prod_mada', None),
                    'date_fin_prevue_prod_mada': getattr(projet, 'date_fin_prevue_prod_mada', None),
                    'date_fin_prod_mada_reelle': getattr(projet, 'date_fin_prod_mada_reelle', None),
                    'etape': etape,
                    'couleur': getattr(projet, 'couleur', '#007bff'),
                    'commercial': f"{projet.commercial.prenoms} {projet.commercial.nom}" if projet.commercial else 'Commercial inconnu',
                    'responsable_ca': f"{projet.responsable_ca.prenoms} {projet.responsable_ca.nom}" if projet.responsable_ca else 'CA inconnu',
                    'date_creation': projet.created_at.isoformat() if projet.created_at else None,
                    'is_complement': False
                })

            except Exception as e:
                print(f"Erreur sur le projet {projet.reference}: {str(e)}")
                # Ajouter quand même le projet avec les données basiques
                projets_data.append({
                    'id': projet.id,
                    'reference': projet.reference,
                    'nom_affaire': getattr(projet, 'nom_affaire', projet.reference),
                    'agence': projet.agence.nom if projet.agence else 'Agence inconnue',
                    'etape': 'Erreur',
                    'couleur': getattr(projet, 'couleur', '#007bff'),
                    'commercial': f"{projet.commercial.prenoms} {projet.commercial.nom}" if projet.commercial else 'Commercial inconnu',
                    'responsable_ca': f"{projet.responsable_ca.prenoms} {projet.responsable_ca.nom}" if projet.responsable_ca else 'CA inconnu',
                })
                continue

        print(f"Projets traités avec succès: {len(projets_data)}")
        print("=== FIN get_projets_prod ===")

        return JsonResponse({'projets': projets_data})

    except Exception as e:
        print(f"ERREUR GLOBALE dans get_projets_prod: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=400)


def get_etape_prod(projet):
    """Détermine l'étape actuelle pour PROD"""
    try:
        etape_envoi_mada = getattr(projet, 'etape_envoi_mada', None)
        etape_reprise_france = getattr(projet, 'etape_reprise_france', None)
        etape_prod_mada = getattr(projet, 'etape_prod_mada', None)
        date_reception_france = getattr(projet, 'date_reception_france', None)
        commentaire_fin_reprise = getattr(projet, 'commentaire_fin_reprise', '')

        print(f"Debug PROD {projet.reference}: envoi_mada={etape_envoi_mada}, date_reception={date_reception_france}, reprise={etape_reprise_france}, commentaire={commentaire_fin_reprise}")

        # CORRECTION : Ajouter le cas etape_envoi_mada = 'en_cours'
        # Étape 1: Réception des données en France (envoi en cours)
        if etape_envoi_mada == 'en_cours' and not date_reception_france and not commentaire_fin_reprise:
            return 'Réception des données en France'

        # Étape 1b: Problème de réception (envoi en cours mais non reçu avec commentaire)
        elif etape_envoi_mada == 'en_cours' and not date_reception_france and commentaire_fin_reprise:
            return 'Problème de réception'

        # Étape 1c: Ancienne logique (pour compatibilité)
        elif etape_envoi_mada == 'termine' and not date_reception_france and not commentaire_fin_reprise:
            return 'Réception des données en France'

        # Étape 1d: Ancienne logique (pour compatibilité)
        elif etape_envoi_mada == 'termine' and not date_reception_france and commentaire_fin_reprise:
            return 'Problème de réception'

        # Étape 2: Après réception OK → Envoie de reprise en France
        elif date_reception_france and etape_reprise_france in [None, 'en_attente']:
            return 'Envoie de reprise en France'

        # Étape 3: Reprise en cours
        elif etape_reprise_france == 'en_cours':
            return 'Reprise en cours'

        # Étape 4: Après reprise terminée → Prod Mada
        elif etape_reprise_france == 'termine' and etape_prod_mada in [None, 'en_attente']:
            return 'Prod en cours Mada'

        # Étape 5: Prod Mada en cours
        elif etape_prod_mada == 'en_cours':
            return 'Prod en cours Mada'

        # Étape 6: Production terminée
        elif etape_prod_mada == 'termine':
            return 'Production terminée'

        # Complément
        reference = getattr(projet, 'reference', '')
        if reference and 'Complément' in reference:
            return 'Complément'

        return 'Non prêt pour PROD'

    except Exception as e:
        print(f"Erreur dans get_etape_prod: {str(e)}")
        return 'Erreur'


@csrf_exempt
@login_required
def reception_donnees(request, projet_id):
    """Gère la réception des données en France"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            statut = data['statut']
            commentaire = data.get('commentaire', '')

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            if statut == 'ok':
                # Marquer comme reçu ET terminé
                projet.date_reception_france = date.today()
                projet.etape_reprise_france = 'en_attente'
                projet.etape_envoi_mada = 'termine'
                projet.commentaire_fin_reprise = ''
                projet.probleme_confirme = False  # Reset le flag
                projet.save()
            else:
                if not commentaire.strip():
                    return JsonResponse({'error': 'Commentaire obligatoire pour "Non reçu"'}, status=400)

                # SAUVEGARDER DANS L'HISTORIQUE AVANT D'ÉCRASER
                if not hasattr(projet, 'historique_commentaires'):
                    projet.historique_commentaires = []

                # Ajouter le commentaire à l'historique avec timestamp
                historique_entry = {
                    'date': date.today().isoformat(),
                    'commentaire': commentaire,
                    'type': 'non_recu',
                    'etape_envoi_mada': projet.etape_envoi_mada
                }
                projet.historique_commentaires.append(historique_entry)

                # Mettre à jour le commentaire actuel
                projet.commentaire_fin_reprise = commentaire
                projet.date_reception_france = None
                # IMPORTANT: Garder etape_envoi_mada à 'en_cours' pour permettre le ré-envoi
                projet.etape_envoi_mada = 'en_cours'
                projet.probleme_confirme = False  # Reset pour nouveau cycle
                projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def envoie_reprise(request, projet_id):
    """Gère l'envoi de reprise en France"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data['action']
            commentaire = data.get('commentaire', '')

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            if action == 'pas':
                # Pas de reprise → Migre à Prod Mada en CA
                projet.etape_reprise_france = 'termine'  # Skip
                projet.etape_prod_mada = 'en_attente'
            else:  # 'faire'
                if not commentaire.strip():
                    return JsonResponse({'error': 'Commentaire obligatoire pour reprise'}, status=400)
                # Créer AO complément
                complement_ref = f"{projet.reference} - Complément"
                complement = AppelOffre.objects.create(
                    reference=complement_ref,
                    nom_affaire=projet.nom_affaire,
                    agence=projet.agence,
                    commercial=projet.commercial,
                    responsable_ca=projet.responsable_ca,
                    description=f"Complément pour {projet.reference}: {commentaire}",
                    couleur=projet.couleur,
                    statut='gagne',
                    etape_reprise_france='en_cours',  # Démarre reprise complément
                    date_debut_reprise=date.today()
                )
                complement.prestations.set(projet.prestations.all())
                # Original passe à prod après complément
                projet.etape_reprise_france = 'termine'  # Temporaire
                projet.commentaire_reprise = commentaire

            projet.save()
            return JsonResponse({'success': True, 'complement_id': complement.id if action == 'faire' else None})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def confirmer_probleme_reception(request, projet_id):
    """Confirme la prise de connaissance d'un problème de réception"""
    if request.method == 'POST':
        try:
            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Marquer que le problème est confirmé
            projet.probleme_confirme = True  # Ajoutez ce champ au modèle si nécessaire
            # OU utiliser un champ existant comme flag
            # projet.etape_envoi_mada = 'confirme'  # Alternative

            projet.save()

            return JsonResponse({'success': True})

        except AppelOffre.DoesNotExist:
            return JsonResponse({'error': 'Projet non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
@login_required
def commencer_prod_mada(request):
    """Démarre la production Mada"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            projet_id = data['projet_id']

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')

            # Validation dates
            date_debut = datetime.strptime(data['date_debut_prod'], '%Y-%m-%d').date()
            date_fin_prevue = datetime.strptime(data['date_fin_prevue_prod'], '%Y-%m-%d').date()

            if date_debut >= date_fin_prevue:
                return JsonResponse({'error': 'Date fin postérieure à début'}, status=400)

            projet.nom_affaire_prod = data['nom_affaire_prod']
            projet.date_debut_prod_mada = date_debut
            projet.date_fin_prevue_prod_mada = date_fin_prevue
            projet.date_debut_prod_mada_reelle = date.today()
            projet.etape_prod_mada = 'en_cours'
            projet.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def fin_prod_mada(request, projet_id):
    """Termine la production Mada"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_fin_reelle = datetime.strptime(data['date_fin_reelle_prod'], '%Y-%m-%d').date()

            projet = AppelOffre.objects.get(id=projet_id, statut='gagne')
            projet.date_fin_prod_mada_reelle = date_fin_reelle
            projet.etape_prod_mada = 'termine'
            projet.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
@login_required
def gestion_complement(request, projet_id):
    """Gère fin reprise ou envoi complément"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data['action']

            complement = AppelOffre.objects.get(id=projet_id, reference__endswith=' - Complément')

            if action == 'fin':
                complement.etape_reprise_france = 'termine'
                complement.date_fin_reprise = date.today()
            else:  # 'envoyer'
                # Similaire à envoyer_donnees_mada
                date_envoi = datetime.strptime(data['date_envoi'], '%Y-%m-%d').date()
                date_livraison = datetime.strptime(data['date_livraison'], '%Y-%m-%d').date()
                complement.date_envoi_mada = date_envoi
                complement.date_livraison_prevue_mada = date_livraison
                complement.info_supplementaire_mada = data.get('info_supplementaire', '')
                complement.etape_envoi_mada = 'termine'
                # Migre original à prod si complément fini
                original = AppelOffre.objects.get(reference=complement.reference.replace(' - Complément', ''))
                original.etape_prod_mada = 'en_attente'

            complement.save()
            original.save() if action == 'envoyer' else None
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)