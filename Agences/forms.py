from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
        required=False,
        help_text="Laissez vide pour utiliser le mot de passe par défaut: groupeparera*25"
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'}),
        required=False
    )

    class Meta:
        model = User
        fields = ('email', 'prenoms', 'pseudo', 'nom', 'agence', 'poste', 'types_prestation')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vos prénoms'}),
            'pseudo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre pseudo'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'agence': forms.Select(attrs={'class': 'form-select'}),
            'poste': forms.Select(attrs={'class': 'form-select'}),
            'types_prestation': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        # Si les deux champs sont vides, utiliser le mot de passe par défaut
        if not password1 and not password2:
            return password2

        # Sinon, valider normalement
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        # Si aucun mot de passe n'est fourni, utiliser le mot de passe par défaut
        if not self.cleaned_data.get('password1'):
            user.set_password('groupeparera*25')
        else:
            user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            if hasattr(self, 'save_m2m'):
                self.save_m2m()
        return user


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'prenoms', 'pseudo', 'nom', 'agence', 'poste', 'types_prestation', 'photo')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'pseudo': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'agence': forms.Select(attrs={'class': 'form-select'}),
            'poste': forms.Select(attrs={'class': 'form-select'}),
            'types_prestation': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class LoginForm(forms.Form):  # ← Changé : forms.Form au lieu de AuthenticationForm
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com',
            'autocomplete': 'email',
            'autofocus': True  # ← Ajouté directement pour l'autofocus
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password'
        })
    )