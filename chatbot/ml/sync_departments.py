"""
Database synchronization script for Aswani Hospital.
Ensures that all 8 supported departments and their specialist doctors
are properly registered in SQLite without modifying or deleting existing records.
"""

import os
import sys
import django

sys_path = r'C:\Users\aswan\OneDrive\Documents\jango\djangotuttorial'
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangotuttorial.settings')
django.setup()

from home.models import Department, Doctor


def sync():
    department_definitions = [
        {
            "canonical_name": "General Medicine",
            "search_names": ["General", "General Medicine"],
            "description": "Comprehensive primary healthcare, routine health exams, fever, infections, and chronic disease management.",
            "doctor": {
                "name": "Dr. Maria George",
                "spec": "General Physician",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Orthopaedics",
            "search_names": ["Orthopedic Surgeon", "Orthopaedics", "Orthopedics"],
            "description": "Specialized diagnosis and surgical care for bones, joints, fractures, ligament tears, and spine conditions.",
            "doctor": {
                "name": "Dr. David Thomas",
                "spec": "Orthopaedic Surgeon",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Cardiology",
            "search_names": ["Cardiology", "Cardiologist"],
            "description": "Advanced heart care, ECG, cardiac evaluations, blood pressure management, and cardiovascular rehabilitation.",
            "doctor": {
                "name": "Dr. John Mathew",
                "spec": "Chief Cardiologist",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Dermatology",
            "search_names": ["Dermatology", "Dermatologist"],
            "description": "Expert skin care, treatments for eczema, acne, psoriasis, allergic rashes, fungal infections, and mole evaluations.",
            "doctor": {
                "name": "Dr. Ananya Sharma",
                "spec": "Consultant Dermatologist",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Neurology",
            "search_names": ["Neurologist", "Neurology"],
            "description": "Specialized care for disorders of the brain, spinal cord, migraine headaches, neuropathy, and peripheral nervous system.",
            "doctor": {
                "name": "Dr. Sarah Joseph",
                "spec": "Senior Neurologist",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "ENT",
            "search_names": ["ENT", "Ear Nose Throat", "Otolaryngology"],
            "description": "Complete diagnosis and treatment for ear infections, hearing loss, sinus congestion, sore throat, and tonsillitis.",
            "doctor": {
                "name": "Dr. Rajesh Kumar",
                "spec": "ENT Specialist & Head-Neck Surgeon",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Paediatrics",
            "search_names": ["Paediatrics", "Pediatrics", "Pediatrician"],
            "description": "Dedicated child healthcare, infant wellness, childhood illnesses, developmental checks, and pediatric immunizations.",
            "doctor": {
                "name": "Dr. Priya Nair",
                "spec": "Senior Paediatrician",
                "img": "doctors/john.jpeg"
            }
        },
        {
            "canonical_name": "Gynaecology",
            "search_names": ["Gynaecology", "Gynecology", "Obstetrics & Gynaecology"],
            "description": "Comprehensive women's healthcare, prenatal and pregnancy consultations, menstrual care, PCOS, and reproductive health.",
            "doctor": {
                "name": "Dr. Lakshmi Menon",
                "spec": "Consultant Obstetrician & Gynaecologist",
                "img": "doctors/john.jpeg"
            }
        },
    ]

    print("Checking and synchronizing hospital departments in SQLite database...")

    for item in department_definitions:
        dept = None
        for s_name in item["search_names"]:
            dept = Department.objects.filter(name__iexact=s_name).first()
            if dept:
                break

        if not dept:
            dept = Department.objects.create(
                name=item["canonical_name"],
                description=item["description"]
            )
            print(f" [+] Created new Department: {dept.name} (ID: {dept.id})")
        else:
            print(f" [OK] Found existing Department in DB: '{dept.name}' (ID: {dept.id})")

        # Check if doctor exists for this department
        doc = Doctor.objects.filter(dep_name=dept).first()
        if not doc:
            doc_info = item["doctor"]
            Doctor.objects.create(
                doc_name=doc_info["name"],
                doc_spec=doc_info["spec"],
                dep_name=dept,
                doc_img=doc_info["img"]
            )
            print(f"     [+] Added doctor: {doc_info['name']} for {dept.name}")
        else:
            print(f"     [OK] Doctor assigned: {doc.doc_name}")

    print("\nAll 8 departments and doctors are synchronized with Django database.")


if __name__ == "__main__":
    sync()
