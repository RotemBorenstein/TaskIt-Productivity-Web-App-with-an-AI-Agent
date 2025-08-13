from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect

def home(request):
    return render(request, "main/home.html", {})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signup:
            auth_login(request, user)
            return redirect('main:tasks')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})



