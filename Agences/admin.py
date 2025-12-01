from datetime import timezone  # ← Ça, c'est le timezone de Python stdlib (une classe pour les fuseaux, sans .now())
from django.utils import timezone as tz  # ← Et là, le bon (Django's), mais aliasé en 'tz'
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
import pandas as pd
from .models import User, Agence, TypePrestation, Poste, AppelOffre, AppelOffreCAProdMada, \
    AppelOffreCARepriseFrance, AppelOffreCAEnvoiMada, AppelOffreCATraitementFrance, AppelOffreCATerrainFrance, \
    AppelOffreCAAOGagne, AppelOffreCommercialPerdu, AppelOffreCommercialGagne, AppelOffreCommercialEnCours, \
    AppelOffreCommercialEnAttente


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'prenoms', 'pseudo')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'prenoms', 'pseudo', 'nom', 'agence', 'poste', 'types_prestation', 'photo')

# Ajoutez ces proxy models dans models.py ou directement dans admin.py
class AppelOffreProdReceptionFrance(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO PROD - 1 - Réception France"
        verbose_name_plural = "AO PROD - 1 - Réception France"

class AppelOffreProdRepriseFrance(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO PROD - 2 - Reprise France"
        verbose_name_plural = "AO PROD - 2 - Reprise France"

class AppelOffreProdEnCoursMada(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO PROD - 3 - Prod Mada en cours"
        verbose_name_plural = "AO PROD - 3 - Prod Mada en cours"

class AppelOffreProdTermine(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO PROD - 4 - Production terminée"
        verbose_name_plural = "AO PROD - 4 - Production terminée"

class AppelOffreProdComplement(AppelOffre):
    class Meta:
        proxy = True
        verbose_name = "AO PROD - Compléments"
        verbose_name_plural = "AO PROD - Compléments"


# ==================== CLASSES ADMIN POUR LES VUES COMMERCIAL FILTRÉES ====================

# ==================== ADMIN POUR LES ÉTAPES PROD ====================

class AppelOffreProdReceptionFranceAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_envoi_mada', 'date_reception_france', 'etape_actuelle')
    list_filter = ('agence', 'date_envoi_mada')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # AO avec envoi Mada terminé mais pas encore reçu en France
        qs = AppelOffre.objects.filter(
            statut='gagne',
            etape_envoi_mada='termine',
            date_reception_france__isnull=True
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "PROD - 1 - Réception France"
        verbose_name_plural = "PROD - 1 - Réception France"


class AppelOffreProdRepriseFranceAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_reception_france', 'date_debut_reprise', 'etape_actuelle')
    list_filter = ('agence', 'date_reception_france')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # AO reçus en France, en attente ou en cours de reprise
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_reception_france__isnull=False,
            etape_reprise_france__in=['en_attente', 'en_cours']
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "PROD - 2 - Reprise France"
        verbose_name_plural = "PROD - 2 - Reprise France"


class AppelOffreProdEnCoursMadaAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_debut_prod_mada', 'date_fin_prevue_prod_mada', 'etape_actuelle')
    list_filter = ('agence', 'date_debut_prod_mada')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # AO en cours de production à Madagascar
        qs = AppelOffre.objects.filter(
            statut='gagne',
            etape_prod_mada='en_cours'
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "PROD - 3 - Prod Mada en cours"
        verbose_name_plural = "PROD - 3 - Prod Mada en cours"


class AppelOffreProdTermineAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_fin_prod_mada_reelle', 'etape_actuelle')
    list_filter = ('agence', 'date_fin_prod_mada_reelle')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # AO avec production Madagascar terminée
        qs = AppelOffre.objects.filter(
            statut='gagne',
            etape_prod_mada='termine'
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "PROD - 4 - Production terminée"
        verbose_name_plural = "PROD - 4 - Production terminée"


class AppelOffreProdComplementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_debut_reprise', 'etape_reprise_france', 'etape_actuelle')
    list_filter = ('agence', 'date_debut_reprise')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Compléments (référence contenant "Complément")
        qs = AppelOffre.objects.filter(
            statut='gagne',
            reference__icontains='Complément'
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "PROD - Compléments"
        verbose_name_plural = "PROD - Compléments"


# ==================== CLASSES ADMIN POUR LES VUES COMMERCIAL FILTRÉES ====================

class AppelOffreCommercialEnAttenteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'commercial', 'responsable_ca', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('agence', 'date_debut', 'date_fin')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        return AppelOffre.objects.filter(statut='en_attente').select_related('agence', 'commercial', 'responsable_ca')

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO Commercial - En Attente"
        verbose_name_plural = "AO Commercial - En Attente"


class AppelOffreCommercialEnCoursAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'commercial', 'responsable_ca', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('agence', 'date_debut', 'date_fin')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        return AppelOffre.objects.filter(statut='en_cours').select_related('agence', 'commercial', 'responsable_ca')

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO Commercial - En Cours"
        verbose_name_plural = "AO Commercial - En Cours"


class AppelOffreCommercialGagneAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'commercial', 'responsable_ca', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('agence', 'date_debut', 'date_fin')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        return AppelOffre.objects.filter(statut='gagne').select_related('agence', 'commercial', 'responsable_ca')

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO Commercial - Gagné"
        verbose_name_plural = "AO Commercial - Gagné"


class AppelOffreCommercialPerduAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'commercial', 'responsable_ca', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('agence', 'date_debut', 'date_fin')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        return AppelOffre.objects.filter(statut='perdu').select_related('agence', 'commercial', 'responsable_ca')

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO Commercial - Perdu"
        verbose_name_plural = "AO Commercial - Perdu"


class AppelOffreCAAOGagneAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'commercial', 'responsable_ca', 'date_debut', 'date_fin', 'created_at', 'etape_actuelle')
    list_filter = ('agence', 'date_debut', 'date_fin')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure TOUS les AO gagnés (trace complète : même ceux avancés dans le workflow)
        qs = AppelOffre.objects.filter(statut='gagne').select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - AO Gagné"
        verbose_name_plural = "AO CA - AO Gagné"


class AppelOffreCATerrainFranceAdmin(admin.ModelAdmin):
    list_display = (
    'reference', 'agence', 'nom_affaire', 'date_debut_terrain', 'date_fin_prevue_terrain', 'responsable_prod_terrain', 'etape_actuelle')
    list_filter = ('agence_terrain', 'date_debut_terrain')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure les AO avec terrain démarré OU terminé (trace : même ceux en traitement/envoi/etc.)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_debut_terrain__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca', 'agence_terrain', 'responsable_prod_terrain')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Terrain France"
        verbose_name_plural = "AO CA - Terrain France"


class AppelOffreCATraitementFranceAdmin(admin.ModelAdmin):
    list_display = (
    'reference', 'agence', 'nom_affaire_traitement', 'date_debut_traitement', 'date_fin_prevue_traitement',
    'responsable_prod_traitement', 'etape_actuelle')
    list_filter = ('agence_traitement', 'date_debut_traitement')
    search_fields = ('reference', 'nom_affaire_traitement', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure les AO avec traitement démarré OU terminé (trace : inclut AO Gagné + Terrain + Traitement + étapes suivantes)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_debut_traitement__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca', 'agence_traitement', 'responsable_prod_traitement')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Traitement France"
        verbose_name_plural = "AO CA - Traitement France"


class AppelOffreCAEnvoiMadaAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_envoi_mada', 'date_livraison_prevue_mada', 'etape_actuelle')
    list_filter = ('agence', 'date_envoi_mada')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure les AO avec envoi démarré OU terminé (trace : inclut toutes les étapes précédentes)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_envoi_mada__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Envoi Mada"
        verbose_name_plural = "AO CA - Envoi Mada"


class AppelOffreCARepriseFranceAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_debut_reprise', 'date_fin_prevue_reprise', 'etape_actuelle')
    list_filter = ('agence', 'date_debut_reprise')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure les AO avec reprise démarrée OU terminée (trace : inclut toutes les étapes précédentes)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_debut_reprise__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Reprise France"
        verbose_name_plural = "AO CA - Reprise France"


class AppelOffreCAProdMadaAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_debut_prod_mada', 'date_fin_prevue_prod_mada', 'etape_actuelle')
    list_filter = ('agence', 'date_debut_prod_mada')
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure les AO avec prod Mada démarrée OU terminée (trace : inclut toutes les étapes précédentes)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_debut_prod_mada__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Prod Mada"
        verbose_name_plural = "AO CA - Prod Mada"


class AppelOffreCATermineAdmin(admin.ModelAdmin):
    list_display = ('reference', 'agence', 'nom_affaire', 'date_fin_prod_mada_reelle', 'etape_actuelle')
    list_filter = ('agence',)
    search_fields = ('reference', 'nom_affaire', 'agence__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')

    def get_queryset(self, request):
        # Inclure TOUS les AO terminés (trace complète)
        qs = AppelOffre.objects.filter(
            statut='gagne',
            date_fin_prod_mada_reelle__isnull=False
        ).select_related('agence', 'commercial', 'responsable_ca')
        return qs

    def etape_actuelle(self, obj):
        # Utiliser la méthode du modèle pour afficher l'étape actuelle
        return obj.get_etape_actuelle()
    etape_actuelle.short_description = "Étape actuelle"

    def has_add_permission(self, request):
        return False

    class Meta:
        verbose_name = "AO CA - Terminé"
        verbose_name_plural = "AO CA - Terminé"


# ==================== ADMIN STANDARD ====================

@admin.register(Agence)
class AgenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_by', 'date_creation', 'membres_count', 'appels_offre_count')
    readonly_fields = ('date_creation',)
    list_filter = ('date_creation',)
    search_fields = ('nom',)
    fieldsets = (
        (None, {
            'fields': ('nom', 'couleur')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'date_creation'),
            'classes': ('collapse',)
        }),
    )

    def membres_count(self, obj):
        return obj.user_set.count()

    membres_count.short_description = "Nombre de membres"

    def appels_offre_count(self, obj):
        return obj.appeloffre_set.count()

    appels_offre_count.short_description = "Appels d'offre"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TypePrestation)
class TypePrestationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_by', 'date_creation', 'utilisateurs_count', 'appels_offre_count')
    readonly_fields = ('date_creation',)
    list_filter = ('date_creation',)
    search_fields = ('nom',)

    def utilisateurs_count(self, obj):
        return obj.user_set.count()

    utilisateurs_count.short_description = "Nombre d'utilisateurs"

    def appels_offre_count(self, obj):
        return obj.appeloffre_set.count()

    appels_offre_count.short_description = "Appels d'offre"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_by', 'date_creation', 'utilisateurs_count', 'commerciaux_count', 'ca_count')
    readonly_fields = ('date_creation',)
    list_filter = ('date_creation',)

    def utilisateurs_count(self, obj):
        return obj.user_set.count()

    utilisateurs_count.short_description = "Nombre d'utilisateurs"

    def commerciaux_count(self, obj):
        if obj.nom == 'COMMERCIAL':
            return obj.user_set.count()
        return '-'

    commerciaux_count.short_description = "Commerciaux"

    def ca_count(self, obj):
        if obj.nom == 'CA':
            return obj.user_set.count()
        return '-'

    ca_count.short_description = "Responsables CA"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = User

    list_display = ('pseudo', 'prenoms', 'email', 'agence', 'poste', 'is_active', 'appels_offre_count')
    list_filter = ('agence', 'poste', 'types_prestation', 'is_active', 'is_staff')
    search_fields = ('pseudo', 'prenoms', 'email', 'nom')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {
            'fields': ('prenoms', 'nom', 'pseudo', 'photo', 'agence', 'poste', 'types_prestation')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'prenoms', 'pseudo', 'password1', 'password2', 'agence', 'poste')}
         ),
    )

    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions', 'types_prestation')

    def appels_offre_count(self, obj):
        count = obj.appels_offre_commercial.count()
        if count > 0:
            return count
        return '-'

    appels_offre_count.short_description = "Appels d'offre"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='import_excel'),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']

            try:
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, header=None)
                else:
                    messages.error(request, "Le fichier doit être au format Excel (.xlsx)")
                    return render(request, 'admin/Agences/user/import_excel.html')

                results = self.process_excel_data(df, request)
                self.display_import_results(request, results)
                return HttpResponseRedirect('../')

            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation : {str(e)}")

        return render(request, 'admin/Agences/user/import_excel.html')

    def process_excel_data(self, df, request):
        results = {
            'created': 0,
            'updated': 0,
            'errors': [],
            'users_processed': set()
        }

        start_row = 1 if df.iloc[0, 0] in ['Nom', 'nom', 'NOM'] else 0

        for index, row in df.iterrows():
            if index < start_row:
                continue

            try:
                nom = str(row[0]).strip() if pd.notna(row[0]) else ""
                prenoms = str(row[1]).strip() if pd.notna(row[1]) else ""
                pseudo = str(row[2]).strip() if pd.notna(row[2]) else ""
                email = str(row[3]).strip() if pd.notna(row[3]) else ""
                type_prestation_nom = str(row[4]).strip() if pd.notna(row[4]) else ""
                poste_nom = str(row[5]).strip() if pd.notna(row[5]) else ""
                agence_nom = str(row[6]).strip() if pd.notna(row[6]) else ""

                if not all([prenoms, pseudo, email]):
                    results['errors'].append(f"Ligne {index + 1}: Champs obligatoires manquants")
                    continue

                user, created = self.get_or_create_user(email, prenoms, pseudo, nom, request)

                if agence_nom:
                    agence, _ = Agence.objects.get_or_create(nom=agence_nom)
                    user.agence = agence

                if poste_nom:
                    poste = self.get_poste(poste_nom)
                    if poste:
                        user.poste = poste

                if type_prestation_nom:
                    type_prestation, _ = TypePrestation.objects.get_or_create(nom=type_prestation_nom)
                    user.types_prestation.add(type_prestation)

                user.save()

                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1

                results['users_processed'].add(email)

            except Exception as e:
                results['errors'].append(f"Ligne {index + 1}: {str(e)}")

        return results

    def get_or_create_user(self, email, prenoms, pseudo, nom, request):
        try:
            user = User.objects.get(email=email)
            created = False
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                prenoms=prenoms,
                pseudo=pseudo,
                password='groupeparera*25'
            )
            created = True

        user.nom = nom or user.nom
        user.prenoms = prenoms or user.prenoms
        user.pseudo = pseudo or user.pseudo

        return user, created

    def get_poste(self, poste_nom):
        poste_mapping = {
            'COMMERCIAL': 'COMMERCIAL',
            'Commercial': 'COMMERCIAL',
            'commercial': 'COMMERCIAL',
            'CA': 'CA',
            'ca': 'CA',
            'PROD': 'PROD',
            'Prod': 'PROD',
            'prod': 'PROD',
            'Production': 'PROD',
            'production': 'PROD'
        }

        poste_code = poste_mapping.get(poste_nom, poste_nom.upper())

        try:
            return Poste.objects.get(nom=poste_code)
        except Poste.DoesNotExist:
            return Poste.objects.create(nom=poste_code)

    def display_import_results(self, request, results):
        if results['created'] > 0:
            messages.success(request, f"{results['created']} utilisateur(s) créé(s) avec succès")
        if results['updated'] > 0:
            messages.success(request, f"{results['updated']} utilisateur(s) mis à jour avec succès")
        if results['errors']:
            for error in results['errors'][:10]:
                messages.error(request, error)
            if len(results['errors']) > 10:
                messages.warning(request, f"... et {len(results['errors']) - 10} autres erreurs")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context=extra_context)


# ==================== INSCRIPTION DES ADMIN PERSONNALISÉS ====================

# On utilise admin.site.register une seule fois pour AppelOffre avec la vue principale
# Les autres vues seront gérées via un ModelAdmin personnalisé avec onglets

class AppelOffreAdmin(admin.ModelAdmin):
    list_display = (
    'reference', 'agence', 'commercial', 'responsable_ca', 'statut', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('statut', 'agence', 'date_debut', 'date_fin', 'created_at')
    search_fields = ('reference', 'agence__nom', 'commercial__prenoms', 'commercial__nom', 'responsable_ca__prenoms',
                     'responsable_ca__nom')
    readonly_fields = ('created_at', 'updated_at', 'reference')
    date_hierarchy = 'created_at'
    filter_horizontal = ('prestations',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'agence', 'commercial', 'responsable_ca', 'statut')
        }),
        ('Dates', {
            'fields': ('date_debut', 'date_fin', 'date_fin_reelle')
        }),
        ('Contenu', {
            'fields': ('prestations', 'description', 'commentaire_arret')
        }),
        ('Apparence', {
            'fields': ('couleur',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('agence', 'commercial', 'responsable_ca').prefetch_related('prestations')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not obj.reference:
                current_year = tz.now().year  # ← tz au lieu de timezone
                last_ao = AppelOffre.objects.filter(
                    created_at__year=current_year
                ).order_by('-id').first()

                next_number = 1
                if last_ao:
                    try:
                        last_number = int(last_ao.reference.split('-')[-1])
                        next_number = last_number + 1
                    except:
                        next_number = 1

                obj.reference = f"AO-{current_year}-{str(next_number).zfill(3)}"

        super().save_model(request, obj, form, change)


# ==================== ACTIONS PERSONNALISÉES ====================

def marquer_comme_gagne(modeladmin, request, queryset):
    queryset.update(statut='gagne', date_fin_reelle=timezone.now())
    messages.success(request, f"{queryset.count()} appel(s) d'offre marqué(s) comme gagné(s)")


marquer_comme_gagne.short_description = "Marquer comme gagné"


def marquer_comme_perdu(modeladmin, request, queryset):
    queryset.update(statut='perdu', date_fin_reelle=timezone.now())
    messages.success(request, f"{queryset.count()} appel(s) d'offre marqué(s) comme perdu(s)")


marquer_comme_perdu.short_description = "Marquer comme perdu"


def remettre_en_cours(modeladmin, request, queryset):
    queryset.update(statut='en_cours', date_fin_reelle=None)
    messages.success(request, f"{queryset.count()} appel(s) d'offre remis en cours")


remettre_en_cours.short_description = "Remettre en cours"

# Ajouter les actions
AppelOffreAdmin.actions = [marquer_comme_gagne, marquer_comme_perdu, remettre_en_cours]

# Enregistrer une seule fois
admin.site.register(AppelOffre, AppelOffreAdmin)

# Enregistrement des proxy models pour l'admin (sections séparées)
admin.site.register(AppelOffreCommercialEnAttente, AppelOffreCommercialEnAttenteAdmin)
admin.site.register(AppelOffreCommercialEnCours, AppelOffreCommercialEnCoursAdmin)
admin.site.register(AppelOffreCommercialGagne, AppelOffreCommercialGagneAdmin)
admin.site.register(AppelOffreCommercialPerdu, AppelOffreCommercialPerduAdmin)

admin.site.register(AppelOffreCAAOGagne, AppelOffreCAAOGagneAdmin)
admin.site.register(AppelOffreCATerrainFrance, AppelOffreCATerrainFranceAdmin)
admin.site.register(AppelOffreCATraitementFrance, AppelOffreCATraitementFranceAdmin)
admin.site.register(AppelOffreCAEnvoiMada, AppelOffreCAEnvoiMadaAdmin)
admin.site.register(AppelOffreCARepriseFrance, AppelOffreCARepriseFranceAdmin)
admin.site.register(AppelOffreCAProdMada, AppelOffreCAProdMadaAdmin)

# Enregistrement des vues PROD
admin.site.register(AppelOffreProdReceptionFrance, AppelOffreProdReceptionFranceAdmin)
admin.site.register(AppelOffreProdRepriseFrance, AppelOffreProdRepriseFranceAdmin)
admin.site.register(AppelOffreProdEnCoursMada, AppelOffreProdEnCoursMadaAdmin)
admin.site.register(AppelOffreProdTermine, AppelOffreProdTermineAdmin)
admin.site.register(AppelOffreProdComplement, AppelOffreProdComplementAdmin)