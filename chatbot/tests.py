"""
Automated Test Suite for Aswani Hospital AI Department Recommendation System.
Tests model inference, API endpoints, emergency detection, database mappings, and booking workflow.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from home.models import Department, Doctor, booking as Booking
from chatbot.ml.recommender import recommend_department


class DepartmentRecommendationModelTests(TestCase):
    """
    Unit tests for the Scikit-learn TF-IDF Machine Learning model and recommender engine.
    """

    def setUp(self):
        # Setup test departments and doctors
        self.dept_cardio = Department.objects.create(
            name="Cardiology",
            description="Cardiology heart care"
        )
        self.doc_cardio = Doctor.objects.create(
            doc_name="Dr. John Mathew",
            doc_spec="Cardiologist",
            dep_name=self.dept_cardio,
            doc_img="doctors/john.jpeg"
        )

        self.dept_ortho = Department.objects.create(
            name="Orthopedic Surgeon",
            description="Orthopaedics bone care"
        )
        self.doc_ortho = Doctor.objects.create(
            doc_name="Dr. David Thomas",
            doc_spec="Orthopaedic Surgeon",
            dep_name=self.dept_ortho,
            doc_img="doctors/john.jpeg"
        )

    def test_orthopaedics_prediction(self):
        result = recommend_department("severe knee joint pain and swelling unable to walk after sports injury")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Orthopaedics")
        self.assertGreater(result["confidence_percentage"], 40.0)
        self.assertIn("booking_url", result["database"])
        self.assertIn("safety_disclaimer", result)

    def test_cardiology_prediction(self):
        result = recommend_department("heavy chest tightness, heart palpitations and breathlessness")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Cardiology")
        self.assertGreater(result["confidence_percentage"], 40.0)

    def test_dermatology_prediction(self):
        result = recommend_department("red itchy skin rash with flaky scaly patches spreading on arms")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Dermatology")

    def test_neurology_prediction(self):
        result = recommend_department("intense throbbing migraine headache with light sensitivity and nausea")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Neurology")

    def test_ent_prediction(self):
        result = recommend_department("severe earache, ringing in ears and difficulty swallowing with sore throat")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "ENT")

    def test_paediatrics_prediction(self):
        result = recommend_department("my 6 month old infant has high fever, crying continuously and refusing milk")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Paediatrics")

    def test_gynaecology_prediction(self):
        result = recommend_department("irregular menstrual cycle, heavy bleeding and severe lower abdominal pelvic cramps")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "Gynaecology")

    def test_general_medicine_prediction(self):
        result = recommend_department("mild viral fever with body chills, extreme tiredness and fatigue")
        self.assertTrue(result["success"])
        self.assertEqual(result["department"], "General Medicine")

    def test_emergency_detection(self):
        result = recommend_department("patient has crushing chest pain and is unable to breathe")
        self.assertTrue(result["success"])
        self.assertTrue(result["is_emergency"])
        self.assertIsNotNone(result["emergency_message"])
        self.assertIn("EMERGENCY", result["emergency_message"].upper())

    def test_empty_input_handling(self):
        result = recommend_department("   ")
        self.assertFalse(result["success"])
        self.assertEqual(result.get("code"), "EMPTY_INPUT")

    def test_short_input_handling(self):
        result = recommend_department("hi")
        self.assertFalse(result["success"])
        self.assertEqual(result.get("code"), "INPUT_TOO_SHORT")


class DepartmentRecommendationAPITests(TestCase):
    """
    Integration tests for the Django API endpoint `/chatbot/api/recommend/`.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("recommend_department_api")

    def test_api_post_json_valid_symptoms(self):
        payload = {"symptoms": "severe knee pain and bone swelling after falling down"}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["department"], "Orthopaedics")
        self.assertIn("confidence_percentage", data)
        self.assertIn("booking_url", data["database"])

    def test_api_get_query_parameter(self):
        response = self.client.get(self.url, {"symptoms": "chest tightness palpitations racing pulse"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["department"], "Cardiology")

    def test_api_post_empty_symptoms_returns_400(self):
        payload = {"symptoms": ""}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_api_post_invalid_json_returns_400(self):
        response = self.client.post(
            self.url,
            data="not a json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])

    def test_chatbot_page_renders_ok(self):
        response = self.client.get(reverse("chatbot"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Hospital")
        self.assertContains(response, "Department Recommender")


class AppointmentBookingWorkflowTests(TestCase):
    """
    End-to-end integration test from recommendation query to preselected doctor booking.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="patient_test",
            password="testpassword123",
            email="patient_test@example.com"
        )
        self.client.login(username="patient_test", password="testpassword123")

        self.dept = Department.objects.create(
            name="Cardiology",
            description="Cardiology"
        )
        self.doctor = Doctor.objects.create(
            doc_name="Dr. Test Cardiologist",
            doc_spec="Cardiologist",
            dep_name=self.dept,
            doc_img="doctors/john.jpeg"
        )

    def test_booking_page_preselects_doctor_from_recommendation(self):
        booking_url = f"/booking/?department_id={self.dept.id}&dept={self.dept.name}"
        response = self.client.get(booking_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["recommended_dept"], "Cardiology")
        # Check initial form doctor is preselected
        form = response.context["form"]
        self.assertEqual(form.initial.get("doc_name"), self.doctor.id)

    def test_complete_booking_submission(self):
        post_data = {
            "p_name": "Test Patient",
            "p_email": "patient_test@example.com",
            "p_phone": "9876543210",
            "doc_name": self.doctor.id,
            "booking_date": "2026-11-15"
        }
        response = self.client.post("/booking/", data=post_data)
        self.assertEqual(response.status_code, 302)  # Redirects to patient_dashboard
        # Verify booking record in SQLite
        b = Booking.objects.filter(p_name="Test Patient").first()
        self.assertIsNotNone(b)
        self.assertEqual(b.doc_name, self.doctor)
        self.assertIsNotNone(b.token_no)
