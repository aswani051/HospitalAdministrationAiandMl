
from django.contrib import admin
from .models import (
    Prescription,
    PrescriptionMedicine,
    MedicinePrice,
    PharmacyBill,
    PharmacyBillItem,
)


admin.site.register(Prescription)
admin.site.register(PrescriptionMedicine)
admin.site.register(MedicinePrice)
admin.site.register(PharmacyBill)
admin.site.register(PharmacyBillItem)