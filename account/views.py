from django.shortcuts import render, redirect, reverse
from django.views import View

from account.models import Otp, User
from .forms import LoginForm, OtpLoginForm, CheckOtpForm, AddressCreationForm
from django.contrib.auth import authenticate, login, logout
import requests
from random import randint
from django.utils.crypto import get_random_string
from uuid import uuid4


# def user_login(request):
#     return render(request, 'account/login.html', {})


class UserLogin(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'account/login.html', {'form': form})
    
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                form.add_error('phone', 'invalid user data')
        else:
            form.add_error('phone', 'invalid data')
        return render(request, 'account/login.html', {'form': form})

class OtpLoginView(View):
    def get(self, request):
        form = OtpLoginForm()
        return render(request, 'account/otp_login.html', {'form': form})
    
    def post(self, request):
        form = OtpLoginForm(request.POST)
        if form.is_valid():
            randcode = randint(1000, 9999)
            cd = form.cleaned_data

            # ارسال SMS
            url = "https://restapi.easysendsms.app/v1/rest/sms/send"
            headers = {
                "apikey": "p7ekr7gm31pqbz7e8ox3tcz59fp3djay",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "from": "Garsivaz",
                "to": cd['phone'],
                "text": f"Hi code is: {randcode}",
                "type": "0"
            }

            # response = requests.post(url, json=data, headers=headers)
            # print(response.status_code, response.json(), randcode)  # فقط برای تست

            token = str(uuid4())
            Otp.objects.create(phone=cd['phone'], code=randcode, token=token)
            print('code:', randcode)
            return redirect(reverse('account:check_otp') + f'?token={token}')

        else:
            form.add_error('phone', 'invalid data')

        return render(request, 'account/otp_login.html', {'form': form})


class CheckOtpView(View):
    def get(self, request):
        form = CheckOtpForm()
        return render(request, 'account/check_otp.html', {'form': form})
    
    def post(self, request):
        token = request.GET.get('token')
        form = CheckOtpForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if Otp.objects.filter(code=cd['code'], token=token).exists():
                otp = Otp.objects.get(token=token)
                user, is_create = User.objects.get_or_create(phone=otp.phone)
                login (request, user, backend='django.contrib.auth.backends.ModelBackend')
                otp.delete()
                return redirect('/')
        else:
            form.add_error('phone', 'invalid data')

        return render(request, 'account/check_otp.html', {'form': form})

class AddAddressView(View):
    def post(self, request):
        form = AddressCreationForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            next_page = request.GET.get('next')
            print('-------------------')
            print(next_page)
            if next_page:
                print('OK')
                return redirect(next_page)
        print('No')

        return render(request, 'account/add_address.html', {'form': form})

    def get (self, request):
        form = AddressCreationForm()
        print('-------------------')
        return render(request, 'account/add_address.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('/')