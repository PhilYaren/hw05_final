from django.contrib.auth import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(forms.UserCreationForm):
    class Meta(forms.UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
