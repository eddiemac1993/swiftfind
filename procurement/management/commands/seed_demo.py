from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from procurement.models import (
    ApprovalStep,
    ClarificationMessage,
    DeliveryNote,
    DocumentNumberSetting,
    GoodsReceivedNote,
    Invoice,
    Notice,
    PaymentRecord,
    ProcurementRequest,
    Product,
    ProductCategory,
    PurchaseOrder,
    Quotation,
    QuotationItem,
    Receipt,
    RequestItem,
    School,
    Supplier,
    UserProfile,
)


class Command(BaseCommand):
    help = "Seed demo schools, suppliers, products, users, and sample procurement orders."

    def handle(self, *args, **options):
        categories = {}
        for name in [
            "Cement",
            "Paint",
            "Plumbing items",
            "Electrical items",
            "Stationery",
            "Furniture",
            "Cleaning materials",
            "Hardware",
        ]:
            categories[name], _ = ProductCategory.objects.get_or_create(name=name)

        products = [
            ("Cement", "50kg cement bag", "bag", "145.00"),
            ("Paint", "20L acrylic paint", "tin", "580.00"),
            ("Plumbing items", "PVC pipe 50mm", "length", "95.00"),
            ("Electrical items", "LED tube light", "each", "65.00"),
            ("Stationery", "A4 copier paper box", "box", "420.00"),
            ("Furniture", "Classroom desk", "each", "850.00"),
            ("Cleaning materials", "Disinfectant 5L", "bottle", "120.00"),
            ("Hardware", "Door lock set", "each", "180.00"),
        ]
        product_map = {}
        for cat, name, unit, price in products:
            product_map[name], _ = Product.objects.get_or_create(
                name=name,
                defaults={"category": categories[cat], "unit": unit, "guide_price": Decimal(price)},
            )

        school_a, _ = School.objects.update_or_create(
            name="Test School",
            defaults={"district": "Lusaka", "province": "Lusaka", "contact_person": "Test School User", "phone": "+260 955 100 100", "email": "testschool@example.com"},
        )
        school_b, _ = School.objects.get_or_create(
            name="Kabwe Central Secondary School",
            defaults={"district": "Kabwe", "province": "Central", "contact_person": "Peter Mwansa", "phone": "+260 966 200 200", "email": "kabwecentral@example.com"},
        )

        supplier_a, _ = Supplier.objects.update_or_create(
            name="Test Supplier",
            defaults={"district": "Lusaka", "contact_person": "Test Supplier User", "phone": "+260 977 300 300", "email": "testsupplier@example.com"},
        )
        supplier_b, _ = Supplier.objects.get_or_create(
            name="Classroom Essentials Zambia",
            defaults={"district": "Kabwe", "contact_person": "Joseph Tembo", "phone": "+260 977 400 400", "email": "quotes@classroom.example"},
        )
        supplier_a.categories.set([categories["Cement"], categories["Paint"], categories["Hardware"], categories["Plumbing items"]])
        supplier_b.categories.set([categories["Stationery"], categories["Furniture"], categories["Cleaning materials"], categories["Electrical items"]])

        users = [
            ("admin", "12345678", UserProfile.ROLE_ADMIN, None, None, True),
            ("school", "12345678", UserProfile.ROLE_SCHOOL, school_a, None, False),
            ("supplier", "12345678", UserProfile.ROLE_SUPPLIER, None, supplier_a, False),
            ("viewer", "Viewer123!", UserProfile.ROLE_VIEWER, None, None, False),
        ]
        for username, password, role, school, supplier, is_staff in users:
            user, created = User.objects.get_or_create(username=username, defaults={"is_staff": is_staff, "is_superuser": username == "admin"})
            user.is_staff = is_staff
            user.is_superuser = username == "admin"
            user.set_password(password)
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={"role": role, "school": school, "supplier": supplier})

        admin_user = User.objects.get(username="admin")
        school_user = User.objects.get(username="school")
        supplier_user = User.objects.get(username="supplier")

        req, _ = ProcurementRequest.objects.get_or_create(
            title="Classroom repairs and maintenance materials",
            school=school_a,
            defaults={
                "status": ProcurementRequest.STATUS_PAID,
                "needed_by": date.today() + timedelta(days=14),
                "quotation_deadline": timezone.now() + timedelta(days=7),
                "selected_supplier": supplier_a,
                "selection_reason": "Best value quotation with the shortest delivery timeline.",
                "delivery_due_date": date.today() + timedelta(days=5),
                "notes": "Urgent materials for classroom block repairs.",
            },
        )
        cement, _ = RequestItem.objects.get_or_create(request=req, product=product_map["50kg cement bag"], defaults={"quantity": 40})
        paint, _ = RequestItem.objects.get_or_create(request=req, product=product_map["20L acrylic paint"], defaults={"quantity": 8})

        quote, _ = Quotation.objects.get_or_create(
            request=req,
            supplier=supplier_a,
            defaults={"quotation_number": "Q-EDU-1001", "valid_until": date.today() + timedelta(days=21), "delivery_days": 5, "is_selected": True},
        )
        quote.is_selected = True
        quote.save(update_fields=["is_selected"])
        QuotationItem.objects.get_or_create(quotation=quote, request_item=cement, defaults={"unit_price": Decimal("140.00")})
        QuotationItem.objects.get_or_create(quotation=quote, request_item=paint, defaults={"unit_price": Decimal("560.00")})

        PurchaseOrder.objects.get_or_create(request=req, defaults={"supplier": supplier_a, "po_number": "PO-2026-0001", "issued_date": date.today(), "confirmed_by_supplier": True})
        DeliveryNote.objects.get_or_create(request=req, defaults={"supplier": supplier_a, "delivery_number": "DN-2026-0001", "delivered_date": date.today(), "items_delivered": "40 bags cement and 8 buckets acrylic paint delivered."})
        GoodsReceivedNote.objects.get_or_create(request=req, defaults={"grn_number": "GRN-2026-0001", "received_date": date.today(), "received_by": "Mary Banda", "condition_notes": "Items received in good condition."})
        Invoice.objects.get_or_create(request=req, defaults={"supplier": supplier_a, "invoice_number": "INV-2026-0001", "invoice_date": date.today(), "amount": Decimal("10080.00")})
        PaymentRecord.objects.get_or_create(request=req, defaults={"status": PaymentRecord.STATUS_PAID, "amount": Decimal("10080.00"), "payment_reference": "TREASURY-001", "paid_date": date.today()})
        Receipt.objects.get_or_create(request=req, defaults={"supplier": supplier_a, "receipt_number": "RCT-2026-0001", "receipt_date": date.today(), "amount": Decimal("10080.00"), "notes": "Payment received in full."})

        for doc_type, prefix in [
            (DocumentNumberSetting.DOC_PO, "PO"),
            (DocumentNumberSetting.DOC_DELIVERY, "DN"),
            (DocumentNumberSetting.DOC_GRN, "GRN"),
            (DocumentNumberSetting.DOC_INVOICE, "INV"),
            (DocumentNumberSetting.DOC_RECEIPT, "RCT"),
        ]:
            DocumentNumberSetting.objects.get_or_create(document_type=doc_type, defaults={"prefix": prefix, "next_number": 2, "padding": 4})

        ApprovalStep.objects.filter(request=req).delete()

        Notice.objects.get_or_create(
            title="Term procurement submissions",
            defaults={
                "body": "Schools should submit procurement requests with complete quantities, preferred delivery dates, and clear item notes before quotation review.",
                "audience": Notice.AUDIENCE_SCHOOLS,
                "is_pinned": True,
                "created_by": admin_user,
            },
        )
        Notice.objects.get_or_create(
            title="Supplier quotation reminder",
            defaults={
                "body": "Suppliers should confirm item availability, delivery timelines, and pricing before submitting quotations for school comparison.",
                "audience": Notice.AUDIENCE_SUPPLIERS,
                "is_pinned": True,
                "created_by": admin_user,
            },
        )
        ClarificationMessage.objects.get_or_create(
            sender=school_user,
            recipient=supplier_user,
            request=req,
            subject="Confirm delivery timing for classroom materials",
            defaults={"body": "Please confirm whether the cement and paint can be delivered within five working days after PO confirmation."},
        )

        self.stdout.write(self.style.SUCCESS("SchoolProcure demo data seeded. Login: admin/12345678, school/12345678, supplier/12345678, viewer/Viewer123!"))
