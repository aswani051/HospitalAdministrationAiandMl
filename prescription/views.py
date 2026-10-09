from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import PrescriptionForm, MedicineFormSet
from .models import Prescription, PrescriptionMedicine

from home.models import Doctor, booking


# =========================================================
# CREATE PRESCRIPTION
# Doctor writes prescription
# =========================================================

@login_required
def create_prescription(request, appointment_id):

    appointment = get_object_or_404(
        booking,
        id=appointment_id
    )

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    if request.method == 'POST':

        prescription_form = PrescriptionForm(
            request.POST
        )

        medicine_formset = MedicineFormSet(
            request.POST,
            queryset=PrescriptionMedicine.objects.none()
        )

        if (
            prescription_form.is_valid()
            and medicine_formset.is_valid()
        ):

            # Create prescription
            prescription = prescription_form.save(
                commit=False
            )

            # Connect prescription to appointment
            prescription.patient = appointment

            # Store patient name
            prescription.patient_name = appointment.p_name

            # New prescription starts as Pending
            prescription.status = 'Pending'

            prescription.save()

            # Save medicines
            medicines = medicine_formset.save(
                commit=False
            )

            for medicine in medicines:

                # Ignore empty rows
                if not medicine.medicine_name.strip():
                    continue

                medicine.prescription = prescription

                medicine.save()

            # After doctor saves,
            # send prescription to pharmacist
            return redirect(
                'doctor_dashboard'
            )

    else:

        prescription_form = PrescriptionForm()

        medicine_formset = MedicineFormSet(
            queryset=PrescriptionMedicine.objects.none()
        )

    return render(
        request,
        'create_prescription.html',
        {
            'prescription_form': prescription_form,
            'medicine_formset': medicine_formset,
            'appointment': appointment,
            'doctor': doctor,
        }
    )


# =========================================================
# PHARMACIST DASHBOARD
# =========================================================

@login_required
def pharmacist_dashboard(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            'patient',
            'patient__doc_name',
            'patient__doc_name__dep_name'
        )
        .prefetch_related(
            'medicines'
        )
        .order_by(
            '-created_at'
        )
    )

    pending_count = prescriptions.filter(
        status='Pending'
    ).count()

    ready_count = prescriptions.filter(
        status='Ready'
    ).count()

    dispatch_count = prescriptions.filter(
        status='Dispatch'
    ).count()

    return render(
        request,
        'pharmacist_dashboard.html',
        {
            'prescriptions': prescriptions,
            'pending_count': pending_count,
            'ready_count': ready_count,
            'dispatch_count': dispatch_count,
        }
    )


# =========================================================
# UPDATE PRESCRIPTION STATUS
# Pharmacist
# =========================================================

@login_required
def update_prescription_status(
    request,
    prescription_id,
    new_status
):

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    allowed_statuses = [
        'Pending',
        'Ready',
        'Dispatch'
    ]

    if new_status in allowed_statuses:

        prescription.status = new_status

        prescription.save()

    return redirect(
        'pharmacist_dashboard'
    )


# =========================================================
# DELETE PRESCRIPTION
# =========================================================

@login_required
def delete_prescription(
    request,
    prescription_id
):

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    prescription.delete()

    return redirect(
        'pharmacist_dashboard'
    )


# =========================================================
# VIEW PRESCRIPTION
# Doctor / Pharmacist / Patient
# =========================================================

@login_required
def view_prescription(
    request,
    prescription_id
):

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    return render(
        request,
        'view_prescription.html',
        {
            'prescription': prescription,
            'appointment': prescription.patient,
        }
    )


# =========================================================
# PATIENT PRESCRIPTION
# =========================================================

@login_required
def patient_prescription(
    request,
    prescription_id
):

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    # Make sure this prescription belongs
    # to the logged-in patient
    if (
        prescription.patient
        and prescription.patient.p_email
        != request.user.email
    ):
        return redirect(
            'patient_dashboard'
        )

    return render(
        request,
        'view_prescription.html',
        {
            'prescription': prescription,
            'appointment': prescription.patient,
        }
    )
