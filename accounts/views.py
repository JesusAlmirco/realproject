from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from accounts.models import User, LoginAttempt
from accounts.forms import RegistrationForm, LoginForm, UserForm
# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib import messages, auth
from django.conf import settings #LOGIN_ATTEMPTS_TIME_LIMIT, MAX_LOGIN_ATTEMPTS
from django.urls import reverse

# User registration
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Por favor activa tu cuenta'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Le hemos enviado un correo electrónico de verificación a su dirección de correo electrónico. Por favor verifíquelo.')
            # return redirect('/accounts/login/?command=verification&email='+email)
            return redirect('login')
        else:
            messages.error(request, 'Ocurrió un error durante el registro.')
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

# User login
def login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            # email = request.POST['email']
            # password = request.POST['password']
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            now = timezone.now()

            try:
                _user = User.objects.get(email=email)
                login_attempt, created = LoginAttempt.objects.get_or_create(user=_user)  # get the user's login attempt
                if (login_attempt.timestamp + timedelta(seconds=settings.LOGIN_ATTEMPTS_TIME_LIMIT)) < now:
                    user = auth.authenticate(email=email, password=password)
                    if user is not None:
                        auth.login(request, user)
                        login_attempt.login_attempts = 0    # reset the login attempts
                        login_attempt.save()
                        messages.success(request, 'Bienvenido, Happy hacking!')
                        return redirect(reverse('accounts:dashboard')) # success login redirect to dashboard

                    else:
                        # if the password is incorrect, increment the login attempts and
                        # if the login attempts == MAX_LOGIN_ATTEMPTS, set the user to be inactive and send activation email
                        login_attempt.login_attempts += 1
                        login_attempt.timestamp = now
                        login_attempt.save()
                        if login_attempt.login_attempts == settings.MAX_LOGIN_ATTEMPTS:
                            _user.is_active = False
                            _user.save()
                            messages.error(request, 'Cuenta suspendida, se excedió el máximo de intentos de inicio de sesión.')
                        else:
                            messages.error(request, 'Email o contraseña incorrecto.')
                            return redirect(reverse('accounts:login'))
                else:
                    messages.error(request, 'Acceso fallido. Por favor intente nuevamente')
                    return redirect(reverse('accounts:login'))

            except User.DoesNotExist:
                messages.error(request, 'Cuenta no existe, registrate.')
                return redirect(reverse('accounts:register'))
        
    context = {
        'form': form
    }
        
    return render(request, 'accounts/login.html', context)

# Logout session
@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'Estás desconectado. Vuelva Pronto')
    return redirect('home')
# Activate account
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, '¡Felicidades! Su cuenta está activada.')
        return redirect('login')
    else:
        messages.error(request, 'Enlace de activación no válido')
        return redirect('register')


# Dashboard
@login_required(login_url = 'login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

# Forgot password
def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Se ha enviado un email para restablecer su contraseña.')
            return redirect('login')
        else:
            messages.error(request, '¡La cuenta no existe!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

# Validate rest password
def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')

# Reset password
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')


# Edit user profile
@login_required(login_url='login')
def edit_profile(request):
    # userprofile = get_object_or_404(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        
    context = {
        'user_form': user_form,
        # 'userprofile': userprofile,
    }
    return render(request, 'accounts/profile.html', context)

# Chnage password
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = User.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Contraseña actualizada exitosamente.')
                return redirect('change_password')
            else:
                messages.error(request, 'Por favor, introduzca una contraseña actual válida')
                return redirect('change_password')
        else:
            messages.error(request, '¡Las contraseñas no coinciden!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')