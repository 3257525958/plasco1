from django.shortcuts import render
from cantact_app.models import accuntmodel
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
def home_def(request):
    login_user = 'false'
    if request.user.is_authenticated:
        login_user = 'true'
    return render(request,'new_home.html',context={
                                                                'login_user':login_user,
                                                                })

def logute(request):
    logout(request)
    return redirect('/')


