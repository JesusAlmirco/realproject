from django import forms
from accounts.models import User

# User Register
class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Ej: john@email.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': "",
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': ""
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "¡Las contraseñas no coinciden!"
            )

    def clean_email(self):
        cleaned_data = super(RegistrationForm, self).clean()
        email = cleaned_data.get('email').lower()
        # email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email):
            raise forms.ValidationError("Correo electrónico en uso, elija otro.")
        return email

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Ej: John'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Ej: Smith'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            
# Login Form
class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: john@email.com'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ''})
    )

# User form
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'