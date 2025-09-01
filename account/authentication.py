from django.contrib.auth.backends import BaseBackend

from account.models import User

class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        print("2-Received phone/email:", username)
        print("2-Received password:", password)
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

            
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
