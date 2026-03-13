from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Choose a unique username',
            'first_name': 'Enter your first name',
            'last_name': 'Enter your last name',
            'email': 'name@example.com',
            'phone_number': 'Enter mobile number',
            'role': 'Select role',
            'password': 'Create a strong password',
            'confirm_password': 'Re-enter your password',
        }

        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]

        self.fields['role'].initial = User.Role.ATTENDEE
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': placeholders['password']})
        self.fields['confirm_password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': placeholders['confirm_password']})

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match.')
        if cleaned_data.get('role') == User.Role.ADMIN:
            raise forms.ValidationError('Admin role cannot be selected.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if user.role == User.Role.ORGANIZER:
            user.is_organizer_approved = False
        if commit:
            user.save()
        return user
