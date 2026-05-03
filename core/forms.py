from django import forms
from datetime import date
from .models import Voter, Election, Candidate


class SignupStep1Form(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'email', 'phone']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 XXXXX XXXXX'}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError('You must be at least 18 years old to register.')
        return dob

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Voter.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class SignupStep2Form(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a strong password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Passwords do not match.')
        if password:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
            if not (has_upper and has_lower and has_digit and has_special):
                raise forms.ValidationError(
                    'Password must contain uppercase, lowercase, digit, and special character.'
                )
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your registered email'})
    )


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'title': forms.TextInput(attrs={'placeholder': 'Election title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description'}),
        }


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['position', 'party', 'full_name', 'affiliation', 'photo', 'bio', 'manifesto', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'affiliation': forms.TextInput(attrs={'placeholder': 'Other affiliation (optional)'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short biography'}),
            'manifesto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Campaign manifesto'}),
        }
