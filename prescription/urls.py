
from django.urls import path

from . import views


urlpatterns = [

    # Doctor
    path(
        'create/<int:appointment_id>/',
        views.create_prescription,
        name='create_prescription'
    ),

    # Pharmacist
    path(
        'dashboard/',
        views.pharmacist_dashboard,
        name='pharmacist_dashboard'
    ),

    path(
        'update-status/<int:prescription_id>/<str:new_status>/',
        views.update_prescription_status,
        name='update_prescription_status'
    ),

    path(
        'delete/<int:prescription_id>/',
        views.delete_prescription,
        name='delete_prescription'
    ),

    # Pharmacy Billing
    path(
        'billing/create/<int:prescription_id>/',
        views.create_pharmacy_bill,
        name='create_pharmacy_bill'
    ),

    path(
        'billing/<int:bill_id>/',
        views.pharmacy_bill_detail,
        name='pharmacy_bill_detail'
    ),

    # View prescription
    path(
        'view/<int:prescription_id>/',
        views.view_prescription,
        name='view_prescription'
    ),

    # Patient
    path(
        'patient/<int:prescription_id>/',
        views.patient_prescription,
        name='patient_prescription'
    ),
]