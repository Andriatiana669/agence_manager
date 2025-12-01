from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User sans username."""

    def create_user(self, email, prenoms, pseudo, password=None, **extra_fields):
        """Crée et retourne un utilisateur avec un email, prénoms et pseudo."""
        if not email:
            raise ValueError('L\'adresse email doit être renseignée')
        if not prenoms:
            raise ValueError('Les prénoms doivent être renseignés')
        if not pseudo:
            raise ValueError('Le pseudo doit être renseigné')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            prenoms=prenoms,
            pseudo=pseudo,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, prenoms, pseudo, password=None, **extra_fields):
        """Crée et retourne un superutilisateur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email, prenoms, pseudo, password, **extra_fields)


class Agence(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    couleur = models.CharField(max_length=7, default='#007bff')  # Nouveau champ
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='agences_crees')
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Agence"
        verbose_name_plural = "Agences"


class TypePrestation(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='prestations_crees')
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Type de Prestation"
        verbose_name_plural = "Types de Prestation"


class Poste(models.Model):
    POSTE_CHOICES = [
        ('COMMERCIAL', 'Commercial'),
        ('CA', 'CA'),
        ('PROD', 'Prod'),
    ]

    nom = models.CharField(max_length=20, choices=POSTE_CHOICES, unique=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='postes_crees')
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.get_nom_display()

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"


class User(AbstractUser):
    # Champs personnalisés
    nom = models.CharField(max_length=100, blank=True, null=True)
    prenoms = models.CharField(max_length=200)
    pseudo = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    agence = models.ForeignKey(Agence, on_delete=models.SET_NULL, null=True, blank=True)
    types_prestation = models.ManyToManyField(TypePrestation, blank=True)
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='photos_profil/', blank=True, null=True)

    # Surcharger le champ username pour utiliser email comme identifiant
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['prenoms', 'pseudo']  # Champs requis pour createsuperuser

    # Utiliser le manager personnalisé
    objects = UserManager()

    def save(self, *args, **kwargs):
        creating = self._state.adding
        if creating and (not self.password or self.password == 'groupeparera*25'):
            self.set_password('groupeparera*25')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prenoms} ({self.pseudo})"


class AppelOffre(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('gagne', 'Gagné'),
        ('perdu', 'Perdu'),
    ]

    # Nouveaux choix pour les étapes CA
    ETAPE_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    # Champs existants
    reference = models.CharField(max_length=50, unique=True)
    agence = models.ForeignKey('Agence', on_delete=models.CASCADE)
    prestations = models.ManyToManyField('TypePrestation')
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    responsable_ca = models.ForeignKey('User', on_delete=models.CASCADE, related_name='appels_offre_ca')
    commercial = models.ForeignKey('User', on_delete=models.CASCADE, related_name='appels_offre_commercial')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    description = models.TextField(blank=True)
    commentaire_arret = models.TextField(blank=True)
    probleme_confirme = models.BooleanField(default=False)
    couleur = models.CharField(max_length=7, default='#007bff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # === NOUVEAUX CHAMPS POUR LE WORKFLOW CA ===

    # Informations générales de l'affaire
    nom_affaire = models.CharField(max_length=200, blank=True, null=True)

    # Phase Terrain France
    date_debut_terrain = models.DateField(null=True, blank=True)
    date_fin_prevue_terrain = models.DateField(null=True, blank=True)
    #date_debut_terrain_reelle = models.DateField(null=True, blank=True)
    date_fin_terrain_reelle = models.DateField(null=True, blank=True)
    etape_terrain_france = models.CharField(max_length=20, choices=ETAPE_CHOICES, default='en_attente')
    agence_terrain = models.ForeignKey('Agence', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='appels_terrain')
    responsable_prod_terrain = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                                 related_name='appels_prod_terrain')
    commentaire_fin_terrain = models.TextField(blank=True)

    # Phase Traitement France
    nom_affaire_traitement = models.CharField(max_length=200, blank=True, null=True)
    date_debut_traitement = models.DateField(null=True, blank=True)
    date_fin_prevue_traitement = models.DateField(null=True, blank=True)

    #date_debut_traitement_reelle = models.DateField(null=True, blank=True)
    date_fin_traitement_reelle = models.DateField(null=True, blank=True)
    etape_traitement_france = models.CharField(max_length=20, choices=ETAPE_CHOICES, default='en_attente')
    agence_traitement = models.ForeignKey('Agence', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='appels_traitement')
    responsable_prod_traitement = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                                    related_name='appels_prod_traitement')
    commentaire_fin_traitement = models.TextField(blank=True)

    # Phase Envoi à Madagascar
    date_envoi_mada = models.DateField(null=True, blank=True)
    date_livraison_prevue_mada = models.DateField(null=True, blank=True)
    date_livraison_reelle_mada = models.DateField(null=True, blank=True)
    etape_envoi_mada = models.CharField(max_length=20, choices=ETAPE_CHOICES, default='en_attente')
    info_supplementaire_mada = models.TextField(blank=True)
    date_reception_france = models.DateField(null=True, blank=True)

    # Phase Reprise des données France
    date_debut_reprise = models.DateField(null=True, blank=True)  # CORRECTION: nom cohérent
    date_fin_prevue_reprise = models.DateField(null=True, blank=True)
    date_fin_reprise_reelle = models.DateField(null=True, blank=True)  # CORRECTION: nom cohérent
    etape_reprise_france = models.CharField(max_length=20, choices=ETAPE_CHOICES, default='en_attente')
    commentaire_fin_reprise = models.TextField(blank=True)  # CORRECTION: nom cohérent
    historique_commentaires = models.JSONField(default=list, blank=True)  # ← NOUVEAU CHAMP

    # Phase Production Madagascar
    date_debut_prod_mada = models.DateField(null=True, blank=True)
    date_fin_prevue_prod_mada = models.DateField(null=True, blank=True)
    date_fin_prod_mada_reelle = models.DateField(null=True, blank=True)  # CORRECTION: nom cohérent
    etape_prod_mada = models.CharField(max_length=20, choices=ETAPE_CHOICES, default='en_attente')
    commentaire_fin_prod_mada = models.TextField(blank=True)  # CORRECTION: nom cohérent

    def __str__(self):
        return self.reference

    class Meta:
        verbose_name = "Appel d'offre"
        verbose_name_plural = "Appels d'offre"

    # Nouvelle méthode pour déterminer l'étape actuelle
    def get_etape_actuelle(self):
        """Retourne l'étape actuelle du projet pour l'affichage"""
        if self.statut != 'gagne':
            return 'Non gagné'

        if not self.date_debut_terrain:
            return 'AO Gagné'
        elif self.date_debut_terrain and not self.date_fin_terrain_reelle:
            return 'Terrain France'
        elif self.date_fin_terrain_reelle and not self.date_debut_traitement:
            return 'Terrain France terminé'
        elif self.date_debut_traitement and not self.date_fin_traitement_reelle:
            return 'Traitement France'
        elif self.date_fin_traitement_reelle and not self.date_envoi_mada:
            return 'Prêt pour envoi Mada'
        elif self.date_envoi_mada and not self.date_debut_reprise:
            return 'Envoi des données à Mada'
        elif self.date_debut_reprise and not self.date_fin_reprise_reelle:
            return 'Reprise des données France'
        elif self.date_fin_reprise_reelle and not self.date_debut_prod_mada:
            return 'Prêt pour production Mada'
        elif self.date_debut_prod_mada and not self.date_fin_prod_mada_reelle:
            return 'Prod en cours Mada'
        elif self.date_fin_prod_mada_reelle:
            return 'Production terminée'
        else:
            return 'En attente'

    # Méthode pour obtenir les responsables prod selon l'étape
    def get_responsable_prod_actuel(self):
        """Retourne le responsable prod actuel selon l'étape"""
        etape = self.get_etape_actuelle()

        if etape in ['AO Gagné', 'Terrain France', 'Terrain France terminé']:
            return self.responsable_prod_terrain
        elif etape in ['Traitement France', 'Prêt pour envoi Mada']:
            return self.responsable_prod_traitement or self.responsable_prod_terrain
        else:
            return self.responsable_prod_traitement or self.responsable_prod_terrain

    # Méthode pour vérifier si le projet est en retard
    def est_en_retard(self):
        """Vérifie si le projet est en retard selon son étape actuelle"""
        today = timezone.now().date()
        etape = self.get_etape_actuelle()

        if etape == 'Terrain France' and self.date_fin_prevue_terrain and self.date_fin_prevue_terrain < today:
            return True
        elif etape == 'Traitement France' and self.date_fin_prevue_traitement and self.date_fin_prevue_traitement < today:
            return True
        elif etape == 'Envoi des données à Mada' and self.date_livraison_prevue_mada and self.date_livraison_prevue_mada < today:
            return True
        elif etape == 'Reprise des données France' and self.date_fin_prevue_reprise and self.date_fin_prevue_reprise < today:
            return True
        elif etape == 'Prod en cours Mada' and self.date_fin_prevue_prod_mada and self.date_fin_prevue_prod_mada < today:
            return True

        return False

    # Méthode pour calculer les jours de retard
    def get_jours_retard(self):
        """Retourne le nombre de jours de retard"""
        if not self.est_en_retard():
            return 0

        today = timezone.now().date()
        etape = self.get_etape_actuelle()

        if etape == 'Terrain France' and self.date_fin_prevue_terrain:
            return (today - self.date_fin_prevue_terrain).days
        elif etape == 'Traitement France' and self.date_fin_prevue_traitement:
            return (today - self.date_fin_prevue_traitement).days
        elif etape == 'Envoi des données à Mada' and self.date_livraison_prevue_mada:
            return (today - self.date_livraison_prevue_mada).days
        elif etape == 'Reprise des données France' and self.date_fin_prevue_reprise:
            return (today - self.date_fin_prevue_reprise).days
        elif etape == 'Prod en cours Mada' and self.date_fin_prevue_prod_mada:
            return (today - self.date_fin_prevue_prod_mada).days

        return 0


# ==================== PROXY MODELS POUR LES VUES SÉPARÉES ====================

# Proxy Models pour les états Commercial
class AppelOffreCommercialEnAttente(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO Commercial - 1 - En Attente"
        verbose_name_plural = "AO Commercial - 1 - En Attente"

    def save(self, *args, **kwargs):
        self.statut = 'en_attente'
        super().save(*args, **kwargs)


class AppelOffreCommercialEnCours(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO Commercial - 2 - En Cours"
        verbose_name_plural = "AO Commercial - 2 - En Cours"

    def save(self, *args, **kwargs):
        self.statut = 'en_cours'
        super().save(*args, **kwargs)


class AppelOffreCommercialGagne(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO Commercial - 3 - Gagné"
        verbose_name_plural = "AO Commercial - 3 - Gagné"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCommercialPerdu(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO Commercial - 4 - Perdu"
        verbose_name_plural = "AO Commercial - 4 - Perdu"

    def save(self, *args, **kwargs):
        self.statut = 'perdu'
        super().save(*args, **kwargs)


# Proxy Models pour les étapes CA
class AppelOffreCAAOGagne(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 1 - AO Gagné"
        verbose_name_plural = "AO CA - 1 - AO Gagné"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCATerrainFrance(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 2 - Terrain France"
        verbose_name_plural = "AO CA - 2 - Terrain France"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCATraitementFrance(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 3 - Traitement France"
        verbose_name_plural = "AO CA - 3 - Traitement France"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCAEnvoiMada(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 4 - Envoi Mada"
        verbose_name_plural = "AO CA - 4 - Envoi Mada"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCARepriseFrance(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 5 - Reprise France"
        verbose_name_plural = "AO CA - 5 - Reprise France"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


class AppelOffreCAProdMada(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO CA - 6 - Prod Mada"
        verbose_name_plural = "AO CA - 6 - Prod Mada"

    def save(self, *args, **kwargs):
        self.statut = 'gagne'
        super().save(*args, **kwargs)


