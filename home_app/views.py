from django.shortcuts import render

def home_def(request):
    return render(request,'new_home.html')