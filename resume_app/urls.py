from django.contrib import admin
from django.urls import path
from resume import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('profile/<int:profile_id>/', views.resume_detail, name='resume_detail'),
    path('upload/', views.upload_resume, name='upload_resume'),
]
