from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
import json

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class ProfileForm(forms.ModelForm):
    # Use CharField to input comma-separated skills & certifications
    skills_str = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Skills (comma-separated)')
    certifications_str = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Certifications (comma-separated)')

    class Meta:
        model = Profile
        fields = ['user_type', 'cgpa', 'experience', 'bio', 'headline', 'location', 'website', 'skills_str', 'certifications_str', 'profile_picture']

    def save(self, commit=True):
        profile = super().save(commit=False)
        # Convert comma-separated string to JSON string for SQLite
        skills_raw = self.cleaned_data.get('skills_str', '')
        profile.set_skills([s.strip() for s in skills_raw.split(',') if s.strip()])

        cert_raw = self.cleaned_data.get('certifications_str', '')
        profile.set_certifications([c.strip() for c in cert_raw.split(',') if c.strip()])

        if commit:
            profile.save()
        return profile
class RegisterProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user_type']

