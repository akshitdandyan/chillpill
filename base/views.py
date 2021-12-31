from django.shortcuts import redirect, render
from .models import Message, Room, Topic
from .form import RoomForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

# rooms_data = [
#     {'id': 1, 'room_name': 'Cool Room'}, 
#     {'id': 2, 'room_name': 'Hot Room'}, 
#     {'id': 3, 'room_name': 'Autumn Room'}, 
#     {'id': 4, 'room_name': 'Spring season'} 
# ]

def login_page(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect("rooms")

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User doesn't exist")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('rooms')
        else:
            messages.error(request, 'Invalid credentials')

    context = { 'page': page}
    return render(request, 'base/login_register.html', context)

def logout_user(request):
    logout(request)
    return redirect('rooms')

def register_page(request):
    page = 'register'
    form = UserCreationForm()

    if(request.method == "POST"):
        form = UserCreationForm(request.POST)
        if(form.is_valid()):
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('rooms')
        else:
            messages.error(request, "Something bad happened while registering you.")

    context = { 'page': page, 'form': form }
    return render(request, 'base/login_register.html', context)

def home(request):
    return render(request, 'base/home.html')

def rooms(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms_from_db = Room.objects.filter(
        Q(topic__name__icontains = q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    rooms_count = rooms_from_db.count()
    topics = Topic.objects.all()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = { 'rooms': rooms_from_db, 'topics': topics, 'rooms_count': rooms_count, 'room_messages': room_messages }
    return render(request, 'base/rooms.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    if request.method == "POST":
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    return render(request, 'base/room.html', { 'room': room , 'room_messages': room_messages, 'participants': participants })

def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topics = Topic.objects.all()
    context={'user': user, 'rooms': rooms, 'room_messages': room_message, 'topics': topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='/login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host=request.user
        #     room.save()
        return redirect('rooms')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def update_room(request, pk):
    room = Room.objects.get(id=int(pk))
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse("You are not allowed to perform this action. ")

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name=request.POST.get('name')
        room.topic=topic
        room.description=request.POST.get('description')
        room.save()
        return redirect('rooms')
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        #     return redirect('rooms')

    context = {'form': form, 'topics': topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def delete_room(request,pk):
    room = Room.objects.get(id=int(pk))

    if request.user != room.host:
        return HttpResponse("You are not allowed to perform this action. ")
    if request.method == 'POST':
        room.delete()
        return redirect('rooms')
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='/login')
def delete_message(request,pk):
    message = Message.objects.get(id=int(pk))

    if request.user != message.user:
        return HttpResponse("You are not allowed to perform this action. ")
    if request.method == 'POST':
        message.delete()
        return redirect('rooms')
    return render(request, 'base/delete.html', {'obj': message})