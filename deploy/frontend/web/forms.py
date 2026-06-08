from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import UserProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ChoiceField(
        choices=UserProfile.AVATAR_CHOICES,
        widget=forms.RadioSelect,
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email", "avatar")

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(user=user, avatar=self.cleaned_data["avatar"])
        return user
