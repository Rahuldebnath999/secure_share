from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from .models import EncryptedFile, Share
from .encryption import encrypt_file, decrypt_file

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64

def home(request):
    return render(request, 'home.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already taken'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('upload')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('upload')
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def _derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt',   # for demo only
        iterations=100_000,
    )
    return kdf.derive(password.encode())

@login_required
def upload(request):
    if request.method == 'POST':
        file = request.FILES['file']
        password = request.POST['password']  # shared secret

        key = _derive_key(password)
        iv_b64, encrypted_b64 = encrypt_file(file.read(), key)

        enc_file = EncryptedFile.objects.create(
            user=request.user,
            filename=file.name,
            iv=iv_b64,
        )
        enc_file.encrypted_file.save(
            f"{file.name}.enc",
            ContentFile(encrypted_b64.encode()),
            save=True,
        )

        share = Share.objects.create(file=enc_file)

        return JsonResponse({
            'share_link': f'/share/{share.token}/',
            'password': password,
        })

    return render(request, 'upload.html')

def share_view(request, token):
    share = get_object_or_404(Share, token=token)

    if share.expires_at < timezone.now() or share.downloads_left <= 0:
        return HttpResponse("Link expired or invalid.", status=404)

    if request.method == 'POST':
        password = request.POST['password']
        key = _derive_key(password)

        encrypted_b64 = share.file.encrypted_file.read().decode()
        decrypted = decrypt_file(encrypted_b64, share.file.iv, key)

        share.downloads_left -= 1
        share.save()

        response = HttpResponse(
            decrypted,
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{share.file.filename}"'
        return response

    return render(request, 'download.html', {
        'token': token,
        'expires': share.expires_at,
    })
