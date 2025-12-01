from django.contrib.auth.backends import ModelBackend
from .models import User

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"Backend called: username='{username}', password_len={len(password) if password else 0}")  # Debug
        if username is None or password is None:
            print("Backend: Missing username or password")
            return None
        try:
            user = User.objects.get(email=username.lower())  # .lower() pour insensibilité case si besoin
            print(f"Backend: User found: {user.email}, is_active: {user.is_active}")
            if user.check_password(password):
                print("Backend: Password match OK")
                return user
            else:
                print("Backend: Password mismatch")
        except User.DoesNotExist:
            print(f"Backend: No user with email '{username}'")
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None