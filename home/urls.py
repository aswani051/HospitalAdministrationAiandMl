from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [

    path('', views.index, name='home'),

    path('about/', views.about, name='about'),

    path('booking/', views.booking, name='booking'),

    path('doctors/', views.doctors, name='doctors'),

    path('contact/', views.contact, name='contact'),

    path('department/', views.department, name='department'),

    path('prescription/', include('prescription.urls')),

    # Patient
    path(
        'patient-dashboard/',
        views.patient_dashboard,
        name='patient_dashboard'
    ),

    path(
        'login/',
        views.patient_login,
        name='login'
    ),

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'ai-patient-assistant/',
        views.ai_patient_assistant,
        name='ai_patient_assistant'
    ),

    # Doctor
    path(
        'doctor-login/',
        views.doctor_login,
        name='doctor_login'
    ),

    path(
        'doctor-dashboard/',
        views.doctor_dashboard,
        name='doctor_dashboard'
    ),

    # Password Reset
    path(
        'forgot-password/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'forgot-password/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path(
    'appointment-status/<int:booking_id>/<str:status>/',
    views.update_appointment_status,
    name='update_appointment_status'
    ),
] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)