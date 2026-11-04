from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import PrescriptionForm, MedicineFormSet
from .models import (
    Prescription,
    PrescriptionMedicine,
    MedicinePrice,
    PharmacyBill,
    PharmacyBillItem,
)

from home.models import Doctor, booking
from django.contrib import messages
from django.db import transaction
from decimal import Decimal, InvalidOperation

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
        .prefetch_related('medicines')
        .order_by('-created_at')
    )

    total_count = prescriptions.count()

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
            'total_count': total_count,
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



@login_required
def create_pharmacy_bill(request, prescription_id):

    prescription = get_object_or_404(
        Prescription.objects.prefetch_related('medicines'),
        id=prescription_id
    )

    prescribed_medicines = prescription.medicines.all()

    if not prescribed_medicines.exists():
        messages.error(
            request,
            "This prescription has no medicines."
        )
        return redirect('pharmacist_dashboard')

    if request.method == 'POST':

        quantities = {}
        bill_items = []
        grand_total = Decimal('0.00')

        try:
            for prescribed in prescribed_medicines:

                quantity_value = request.POST.get(
                    f'quantity_{prescribed.id}', ''
                ).strip()

                if not quantity_value.isdigit():
                    raise ValueError(
                        f"Enter a valid quantity for "
                        f"{prescribed.medicine_name}."
                    )

                quantity = int(quantity_value)

                if quantity < 1:
                    raise ValueError(
                        "Quantity must be at least 1."
                    )

                medicine_price = MedicinePrice.objects.filter(
                    medicine_name__iexact=prescribed.medicine_name.strip()
                ).first()

                if medicine_price is None:
                    raise ValueError(
                        f"Price not found for "
                        f"{prescribed.medicine_name}. "
                        "Add its price in the admin panel first."
                    )

                unit_price = medicine_price.unit_price
                total_price = unit_price * quantity

                quantities[prescribed.id] = quantity

                bill_items.append({
                    'medicine': medicine_price,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                })

                grand_total += total_price

            with transaction.atomic():

                bill, created = PharmacyBill.objects.get_or_create(
                    prescription=prescription
                )

                # Replace previous bill items if regenerated
                bill.items.all().delete()

                for item in bill_items:
                    PharmacyBillItem.objects.create(
                        bill=bill,
                        medicine=item['medicine'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        total_price=item['total_price'],
                    )

                bill.grand_total = grand_total
                bill.save(update_fields=['grand_total'])

            return redirect(
                'pharmacy_bill_detail',
                bill_id=bill.id
            )

        except (ValueError, InvalidOperation) as error:
            messages.error(request, str(error))

    price_map = {
        price.medicine_name.casefold(): price
        for price in MedicinePrice.objects.all()
    }

    medicine_rows = []

    for prescribed in prescribed_medicines:
        price = price_map.get(
            prescribed.medicine_name.strip().casefold()
        )

        medicine_rows.append({
            'prescribed': prescribed,
            'price': price,
        })

    return render(
        request,
        'pharmacy/create_bill.html',
        {
            'prescription': prescription,
            'medicine_rows': medicine_rows,
        }
    )



@login_required
def pharmacy_bill_detail(request, bill_id):

    bill = get_object_or_404(
        PharmacyBill.objects
        .select_related('prescription', 'prescription__patient')
        .prefetch_related('items__medicine'),
        id=bill_id
    )

    return render(
        request,
        'pharmacy/bill_detail.html',
        {
            'bill': bill,
        }
    )