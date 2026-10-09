from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import bookingform, PrescriptionForm
from .models import Department, Doctor, booking as Booking

from prescription.models import Prescription
from prescription.gemini_service import patient_assistant


# =========================================================
# HOME
# =========================================================

def index(request):
    return render(request, 'index.html')


# =========================================================
# ABOUT
# =========================================================

def about(request):
    return render(request, 'about.html')


# =========================================================
# BOOKING
# =========================================================

@login_required(login_url='login')
def booking(request):

    if request.method == 'POST':

        form = bookingform(request.POST)

        if form.is_valid():

            patient = form.save()

            request.session['token_no'] = patient.token_no

            return redirect('patient_dashboard')

    else:

        form = bookingform(
            initial={
                'p_email': request.user.email
            }
        )

    return render(
        request,
        'booking.html',
        {
            'form': form
        }
    )


# =========================================================
# DOCTORS
# =========================================================

def doctors(request):

    dict_doc = {
        'doctors': Doctor.objects.all()
    }

    return render(
        request,
        'doctors.html',
        dict_doc
    )


# =========================================================
# CONTACT
# =========================================================

def contact(request):

    return render(
        request,
        'contact.html'
    )


# =========================================================
# DEPARTMENT
# =========================================================

def department(request):

    depts = Department.objects.all()

    return render(
        request,
        'department.html',
        {
            'depts': depts
        }
    )


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@login_required(login_url='login')
def patient_dashboard(request):

    patient_email = request.user.email

    # Get latest appointment of logged-in patient
    patient_booking = (
        Booking.objects
        .filter(
            p_email=patient_email
        )
        .select_related(
            'doc_name',
            'doc_name__dep_name'
        )
        .order_by(
            '-booked_on'
        )
        .first()
    )

    # Get patient's prescriptions
    prescriptions = Prescription.objects.filter(
        patient_name=request.user.username
    ).order_by(
        '-id'
    )

    return render(
        request,
        'patient_dashboard.html',
        {
            'patient_booking': patient_booking,
            'prescriptions': prescriptions,
        }
    )


# =========================================================
# PATIENT LOGIN
# =========================================================
def patient_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        print("USERNAME:", username)
        print("PASSWORD RECEIVED:", bool(password))

        user = authenticate(
            request,
            username=username,
            password=password
        )

        print("AUTH USER:", user)

        if user is not None:

            login(request, user)

            return redirect('patient_dashboard')

        messages.error(
            request,
            'Invalid email or password.'
        )

    return render(
        request,
        'login.html'
    )

# =========================================================
# DOCTOR LOGIN
# =========================================================

def doctor_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            doctor = Doctor.objects.filter(
                user=user
            ).first()

            if doctor:

                login(
                    request,
                    user
                )

                return redirect(
                    'doctor_dashboard'
                )

            messages.error(
                request,
                'This account is not registered as a doctor.'
            )

        else:

            messages.error(
                request,
                'Invalid username or password.'
            )

    return render(
        request,
        'doctor_login.html'
    )


# =========================================================
# PROFILE
# =========================================================

@login_required(login_url='login')
def profile(request):

    return render(
        request,
        'profile.html'
    )


# =========================================================
# AI PATIENT ASSISTANT
# =========================================================

@login_required(login_url='login')
def ai_patient_assistant(request):

    response = None
    symptoms = ""

    if request.method == 'POST':

        symptoms = request.POST.get(
            'symptoms',
            ''
        ).strip()

        if symptoms:

            try:

                response = patient_assistant(
                    symptoms
                )

            except Exception as e:

                response = f"AI Error: {str(e)}"

    return render(
        request,
        'ai_patient_assistant.html',
        {
            'response': response,
            'symptoms': symptoms,
        }
    )


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

@login_required(login_url='doctor_login')
def doctor_dashboard(request):

    doctor = Doctor.objects.filter(
        user=request.user
    ).first()

    appointments = Booking.objects.filter(
        doc_name=doctor
    ).order_by(
        '-booking_date',
        '-booked_on'
    )

    return render(
        request,
        'doctor_dashboard.html',
        {
            'doctor': doctor,
            'appointments': appointments,
        }
    )


# =========================================================
# UPDATE APPOINTMENT STATUS
# =========================================================

@login_required(login_url='doctor_login')
def update_appointment_status(
    request,
    booking_id,
    status
):

    doctor = Doctor.objects.filter(
        user=request.user
    ).first()

    appointment = Booking.objects.get(
        id=booking_id,
        doc_name=doctor
    )

    allowed_statuses = [
        'Pending',
        'Confirmed',
        'Completed',
        'Cancelled'
    ]

    if status in allowed_statuses:

        appointment.status = status

        appointment.save()

    return redirect(
        'doctor_dashboard'
    )


# =========================================================
# PATIENT REGISTRATION
# =========================================================
def patient_login(request):

    if request.method == 'POST':

        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            next_url = request.POST.get('next')

            if next_url:
                return redirect(next_url)

            return redirect('patient_dashboard')

        messages.error(
            request,
            'Invalid email or password.'
        )

    return render(
        request,
        'login.html'
    )
def register(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(
                request,
                'Passwords do not match.'
            )
            return render(
                request,
                'register.html'
            )

        if User.objects.filter(
            username=email
        ).exists():

            messages.error(
                request,
                'An account with this email already exists.'
            )
            return render(
                request,
                'register.html'
            )

        User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        messages.success(
            request,
            'Registration successful. Please login.'
        )

        return redirect('login')

    return render(
        request,
        'register.html'
    )