from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from sharing import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('upload/', views.upload, name='upload'),
    path('share/<str:token>/', views.share_view, name='share'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
