import json
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from .forms import (
    ApprovalStepForm,
    ClarificationMessageForm,
    DeliveryNoteForm,
    DocumentNumberSettingForm,
    GoodsReceivedNoteForm,
    InvoiceForm,
    PaymentRecordForm,
    ProcurementRequestForm,
    PurchaseOrderForm,
    QuotationForm,
    QuotationItemFormSet,
    QuotationSelectionForm,
    ReceiptForm,
    RequestItemFormSet,
    SchoolForm,
    SupplierForm,
)
from .models import (
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
    PurchaseOrder,
    Quotation,
    Receipt,
    RequestItem,
    School,
    Supplier,
    UserProfile,
)


def role_for(user):
    if user.is_superuser:
        return UserProfile.ROLE_ADMIN
    profile = getattr(user, "profile", None)
    return profile.role if profile else UserProfile.ROLE_VIEWER


def can_edit(user):
    return role_for(user) in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_SCHOOL, UserProfile.ROLE_SUPPLIER}


def visible_requests(user):
    qs = ProcurementRequest.objects.select_related("school", "selected_supplier").prefetch_related("items", "quotations")
    role = role_for(user)
    profile = getattr(user, "profile", None)
    if role == UserProfile.ROLE_SCHOOL and profile and profile.school:
        return qs.filter(school=profile.school)
    if role == UserProfile.ROLE_SUPPLIER and profile and profile.supplier:
        return qs.filter(
            Q(status__in=[ProcurementRequest.STATUS_REQUESTED, ProcurementRequest.STATUS_QUOTED])
            | Q(selected_supplier=profile.supplier)
        )
    return qs


def open_quotation_requests(user):
    return visible_requests(user).filter(
        status__in=[ProcurementRequest.STATUS_REQUESTED, ProcurementRequest.STATUS_QUOTED],
    ).filter(Q(quotation_deadline__isnull=True) | Q(quotation_deadline__gte=timezone.now()))


def selected_supplier_requests(user):
    qs = visible_requests(user).filter(selected_supplier__isnull=False)
    supplier = locked_supplier_for(user)
    if supplier:
        qs = qs.filter(selected_supplier=supplier)
    return qs


def require_editor(user):
    if not can_edit(user):
        return HttpResponseForbidden("This role can view reports but cannot edit school transactions.")
    return None


def require_admin(user):
    if role_for(user) != UserProfile.ROLE_ADMIN:
        return HttpResponseForbidden("Only admins can manage schools and suppliers.")
    return None


def create_linked_user(username, password, email, role, school=None, supplier=None):
    if not username:
        return None
    user = User.objects.create_user(username=username, password=password, email=email or "")
    UserProfile.objects.update_or_create(
        user=user,
        defaults={"role": role, "school": school, "supplier": supplier},
    )
    return user


def notify_user(user, subject, body):
    if not user or not user.email:
        return
    success = False
    error = ""
    try:
        send_mail(subject, body, "noreply@schoolprocure.local", [user.email], fail_silently=False)
        success = True
    except Exception as exc:
        error = str(exc)
    EmailNotification.objects.create(
        recipient=user.email,
        subject=subject,
        body=body,
        sent_successfully=success,
        error_message=error,
    )


def create_default_approvals(req):
    return None


def locked_school_for(user):
    profile = getattr(user, "profile", None)
    if role_for(user) == UserProfile.ROLE_SCHOOL and profile and profile.school:
        return profile.school
    return None


def locked_supplier_for(user):
    profile = getattr(user, "profile", None)
    if role_for(user) == UserProfile.ROLE_SUPPLIER and profile and profile.supplier:
        return profile.supplier
    return None


def generate_doc_number(document_type, fallback_prefix):
    setting, _ = DocumentNumberSetting.objects.get_or_create(
        document_type=document_type,
        defaults={"prefix": fallback_prefix, "next_number": 1, "padding": 4},
    )
    return setting.generate_number()


def preview_doc_number(document_type, fallback_prefix):
    setting, _ = DocumentNumberSetting.objects.get_or_create(
        document_type=document_type,
        defaults={"prefix": fallback_prefix, "next_number": 1, "padding": 4},
    )
    return f"{setting.prefix}-{setting.next_number:0{setting.padding}d}"


def apply_request_filters(qs, params):
    q = params.get("q", "").strip()
    status = params.get("status", "").strip()
    school = params.get("school", "").strip()
    supplier = params.get("supplier", "").strip()
    if q:
        qs = qs.filter(Q(reference__icontains=q) | Q(title__icontains=q) | Q(notes__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if school:
        qs = qs.filter(school_id=school)
    if supplier:
        qs = qs.filter(selected_supplier_id=supplier)
    return qs


@login_required
def dashboard(request):
    requests = visible_requests(request.user)
    line_total = ExpressionWrapper(
        F("items__request_item__quantity") * F("items__unit_price"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    selected_items = Quotation.objects.filter(is_selected=True, request__in=requests)
    context = {
        "total_requests": requests.count(),
        "pending_quotations": requests.filter(status=ProcurementRequest.STATUS_REQUESTED).count(),
        "pos_issued": requests.filter(status=ProcurementRequest.STATUS_PO_ISSUED).count(),
        "delivered_orders": requests.filter(status__in=[
            ProcurementRequest.STATUS_DELIVERED,
            ProcurementRequest.STATUS_GRN_CONFIRMED,
            ProcurementRequest.STATUS_INVOICED,
            ProcurementRequest.STATUS_PAYMENT_PROCESSING,
            ProcurementRequest.STATUS_PAID,
        ]).count(),
        "payments_processing": requests.filter(status=ProcurementRequest.STATUS_PAYMENT_PROCESSING).count(),
        "paid_orders": requests.filter(status=ProcurementRequest.STATUS_PAID).count(),
        "recent_requests": requests[:8],
        "spending_by_school": selected_items.values("request__school__name").annotate(total=Sum(line_total)).order_by("-total")[:8],
        "spending_by_supplier": selected_items.values("supplier__name").annotate(total=Sum(line_total)).order_by("-total")[:8],
        "spending_by_district": selected_items.values("request__school__district").annotate(total=Sum(line_total)).order_by("-total")[:8],
        "spending_by_category": selected_items.values("items__request_item__product__category__name").annotate(total=Sum(line_total)).order_by("-total")[:8],
        "role": role_for(request.user),
        "quotes_to_approve": requests.filter(status=ProcurementRequest.STATUS_QUOTED).prefetch_related("quotations")[:5],
        "unread_messages": ClarificationMessage.objects.filter(recipient=request.user, is_read=False).count(),
    }
    return render(request, "procurement/dashboard.html", context)


@login_required
def requests_list(request):
    reqs = apply_request_filters(visible_requests(request.user), request.GET)
    context = {
        "requests": reqs,
        "schools": School.objects.all(),
        "suppliers": Supplier.objects.all(),
        "statuses": ProcurementRequest.STATUS_CHOICES,
        "filters": request.GET,
    }
    return render(request, "procurement/requests_list.html", context)


@login_required
def schools_list(request):
    q = request.GET.get("q", "").strip()
    district = request.GET.get("district", "").strip()
    schools = School.objects.all()
    if q:
        schools = schools.filter(Q(name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))
    if district:
        schools = schools.filter(district__icontains=district)
    return render(request, "procurement/schools_list.html", {"schools": schools, "filters": request.GET})


@login_required
def school_create(request):
    forbidden = require_admin(request.user)
    if forbidden:
        return forbidden
    if request.method == "POST":
        form = SchoolForm(request.POST)
        if form.is_valid():
            school = form.save()
            user = create_linked_user(
                form.cleaned_data.get("username"),
                form.cleaned_data.get("password"),
                school.email,
                UserProfile.ROLE_SCHOOL,
                school=school,
            )
            if user:
                messages.success(request, f"{school.name} and login user {user.username} were created.")
            else:
                messages.success(request, f"{school.name} was added.")
            return redirect("schools_list")
    else:
        form = SchoolForm()
    return render(request, "procurement/entity_form.html", {"form": form, "title": "Add school", "back_url": reverse("schools_list")})


@login_required
def suppliers_list(request):
    suppliers = Supplier.objects.prefetch_related("categories")
    q = request.GET.get("q", "").strip()
    district = request.GET.get("district", "").strip()
    if q:
        suppliers = suppliers.filter(Q(name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))
    if district:
        suppliers = suppliers.filter(district__icontains=district)
    return render(request, "procurement/suppliers_list.html", {"suppliers": suppliers, "filters": request.GET})


@login_required
def supplier_create(request):
    forbidden = require_admin(request.user)
    if forbidden:
        return forbidden
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            user = create_linked_user(
                form.cleaned_data.get("username"),
                form.cleaned_data.get("password"),
                supplier.email,
                UserProfile.ROLE_SUPPLIER,
                supplier=supplier,
            )
            if user:
                messages.success(request, f"{supplier.name} and login user {user.username} were created.")
            else:
                messages.success(request, f"{supplier.name} was added.")
            return redirect("suppliers_list")
    else:
        form = SupplierForm()
    return render(request, "procurement/entity_form.html", {"form": form, "title": "Add supplier", "back_url": reverse("suppliers_list")})


@login_required
def product_catalogue(request):
    products = Product.objects.select_related("category").filter(is_active=True)
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category:
        products = products.filter(category_id=category)
    from .models import ProductCategory
    categories = ProductCategory.objects.all()
    return render(request, "procurement/product_catalogue.html", {"products": products, "categories": categories, "filters": request.GET})


def visible_notices(user):
    role = role_for(user)
    audiences = [Notice.AUDIENCE_ALL]
    if role == UserProfile.ROLE_SCHOOL:
        audiences.append(Notice.AUDIENCE_SCHOOLS)
    elif role == UserProfile.ROLE_SUPPLIER:
        audiences.append(Notice.AUDIENCE_SUPPLIERS)
    elif role == UserProfile.ROLE_VIEWER:
        audiences.append(Notice.AUDIENCE_VIEWERS)
    else:
        audiences.extend([Notice.AUDIENCE_SCHOOLS, Notice.AUDIENCE_SUPPLIERS, Notice.AUDIENCE_VIEWERS])
    return Notice.objects.filter(is_active=True, audience__in=audiences)


@login_required
def procurement_request_create(request):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    instance = ProcurementRequest(created_by=request.user)
    locked_school = locked_school_for(request.user)
    if locked_school:
        instance.school = locked_school
    if request.method == "POST":
        form = ProcurementRequestForm(request.POST, instance=instance, locked_school=locked_school)
        formset = RequestItemFormSet(request.POST, instance=instance)
        if form.is_valid() and formset.is_valid():
            req = form.save(commit=False)
            req.created_by = request.user
            req.status = ProcurementRequest.STATUS_REQUESTED
            req.save()
            formset.instance = req
            formset.save()
            create_default_approvals(req)
            for user in User.objects.filter(profile__role=UserProfile.ROLE_SUPPLIER):
                notify_user(user, "New procurement request", f"{req.reference} is available for quotation.")
            messages.success(request, "Procurement request submitted to suppliers.")
            return redirect("request_detail", pk=req.pk)
    else:
        form = ProcurementRequestForm(instance=instance, locked_school=locked_school)
        formset = RequestItemFormSet(instance=instance)
    return render(request, "procurement/request_form.html", {"form": form, "formset": formset, "locked_school": locked_school})


@login_required
def request_detail(request, pk):
    req = get_object_or_404(visible_requests(request.user), pk=pk)
    days_remaining = None
    if req.delivery_due_date:
        days_remaining = (req.delivery_due_date - timezone.localdate()).days
    return render(request, "procurement/request_detail.html", {"req": req, "days_remaining": days_remaining})


@login_required
def quotation_create(request):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    locked_supplier = locked_supplier_for(request.user)
    request_queryset = open_quotation_requests(request.user)
    if request.method == "POST":
        form = QuotationForm(request.POST, locked_supplier=locked_supplier, request_queryset=request_queryset)
        if form.is_valid():
            if form.cleaned_data["request"].quotation_deadline and form.cleaned_data["request"].quotation_deadline < timezone.now():
                form.add_error("request", "This request has passed its quotation deadline.")
            else:
                quote = form.save()
                for item in quote.request.items.all():
                    quote.items.get_or_create(request_item=item, defaults={"unit_price": item.product.guide_price})
                quote.request.status = ProcurementRequest.STATUS_QUOTED
                quote.request.save(update_fields=["status"])
                notify_user(quote.request.created_by, "Quotation submitted", f"{quote.supplier.name} submitted quotation {quote.quotation_number} for {quote.request.reference}.")
                messages.info(request, "Add or adjust item pricing for the quotation.")
                return redirect("quotation_edit", pk=quote.pk)
    else:
        initial = {}
        if locked_supplier:
            initial["supplier"] = locked_supplier
        form = QuotationForm(initial=initial, locked_supplier=locked_supplier, request_queryset=request_queryset)
    return render(request, "procurement/quotation_form.html", {"form": form, "locked_supplier": locked_supplier, "open_request_count": request_queryset.count()})


@login_required
def quotation_edit(request, pk):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    quote = get_object_or_404(Quotation.objects.select_related("request", "supplier"), pk=pk)
    supplier = locked_supplier_for(request.user)
    if supplier and quote.supplier_id != supplier.id:
        return HttpResponseForbidden("You can only edit quotations for your supplier account.")
    if quote.request.quotation_deadline and quote.request.quotation_deadline < timezone.now():
        return HttpResponseForbidden("This request has passed its quotation deadline.")
    if request.method == "POST":
        formset = QuotationItemFormSet(request.POST, instance=quote)
        if formset.is_valid():
            formset.save()
            quote.request.status = ProcurementRequest.STATUS_QUOTED
            quote.request.save(update_fields=["status"])
            messages.success(request, "Quotation pricing saved.")
            return redirect("compare_quotations", pk=quote.request.pk)
    else:
        formset = QuotationItemFormSet(instance=quote)
    return render(request, "procurement/quotation_edit.html", {"quote": quote, "formset": formset})


@login_required
def compare_quotations(request, pk):
    req = get_object_or_404(visible_requests(request.user), pk=pk)
    return render(request, "procurement/compare_quotations.html", {"req": req, "selection_form": QuotationSelectionForm()})


@login_required
def select_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    role = role_for(request.user)
    profile = getattr(request.user, "profile", None)
    if role not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_SCHOOL}:
        return HttpResponseForbidden("Only the school user or admin can approve a quotation.")
    if role == UserProfile.ROLE_SCHOOL and (not profile or quotation.request.school_id != getattr(profile.school, "id", None)):
        return HttpResponseForbidden("You can only approve quotations for your assigned school.")
    if request.method == "POST":
        form = QuotationSelectionForm(request.POST)
        if form.is_valid():
            Quotation.objects.filter(request=quotation.request).update(is_selected=False)
            quotation.is_selected = True
            quotation.save(update_fields=["is_selected"])
            quotation.request.selected_supplier = quotation.supplier
            quotation.request.selection_reason = form.cleaned_data["selection_reason"]
            quotation.request.delivery_due_date = timezone.localdate() + timedelta(days=quotation.delivery_days)
            quotation.request.status = ProcurementRequest.STATUS_PO_ISSUED
            quotation.request.save(update_fields=["selected_supplier", "selection_reason", "delivery_due_date", "status"])
            messages.success(request, f"{quotation.supplier.name} quotation approved. Expected delivery is {quotation.request.delivery_due_date:%d %b %Y}.")
        else:
            messages.error(request, "Please enter the reason for selecting this supplier.")
    return redirect("compare_quotations", pk=quotation.request.pk)


@login_required
def purchase_order_upload(request):
    if request.method == "GET":
        initial = {"po_number": preview_doc_number(DocumentNumberSetting.DOC_PO, "PO")}
        request_queryset = selected_supplier_requests(request.user)
        form = PurchaseOrderForm(initial=initial, request_queryset=request_queryset)
        records = PurchaseOrder.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
        return render(request, "procurement/purchase_order_page.html", {"form": form, "records": records})
    return handle_document_form(
        request,
        PurchaseOrderForm,
        PurchaseOrder,
        "procurement/purchase_order_page.html",
        ProcurementRequest.STATUS_PO_ISSUED,
        "Purchase Order saved.",
    )


@login_required
def confirm_purchase_order(request, pk):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    po = get_object_or_404(PurchaseOrder.objects.filter(request__in=visible_requests(request.user)), pk=pk)
    if request.method == "POST":
        po.confirmed_by_supplier = True
        po.confirmed_at = timezone.now()
        po.save(update_fields=["confirmed_by_supplier", "confirmed_at"])
        po.request.status = ProcurementRequest.STATUS_CONFIRMED
        po.request.save(update_fields=["status"])
        messages.success(request, "Purchase Order confirmed by supplier.")
    return redirect("purchase_order_upload")


@login_required
def delivery_note_page(request):
    if request.method == "GET":
        request_queryset = selected_supplier_requests(request.user)
        form = DeliveryNoteForm(
            initial={"delivery_number": preview_doc_number(DocumentNumberSetting.DOC_DELIVERY, "DN")},
            request_queryset=request_queryset,
            supplier=locked_supplier_for(request.user),
        )
        records = DeliveryNote.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
        return render(request, "procurement/delivery_note_page.html", {"form": form, "records": records})
    return handle_document_form(
        request,
        DeliveryNoteForm,
        DeliveryNote,
        "procurement/delivery_note_page.html",
        ProcurementRequest.STATUS_DELIVERED,
        "Delivery note recorded.",
    )


@login_required
def goods_received_page(request):
    if request.method == "GET":
        form = GoodsReceivedNoteForm(
            initial={"grn_number": preview_doc_number(DocumentNumberSetting.DOC_GRN, "GRN")},
            request_queryset=selected_supplier_requests(request.user),
        )
        records = GoodsReceivedNote.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
        return render(request, "procurement/goods_received_page.html", {"form": form, "records": records})
    return handle_document_form(
        request,
        GoodsReceivedNoteForm,
        GoodsReceivedNote,
        "procurement/goods_received_page.html",
        ProcurementRequest.STATUS_GRN_CONFIRMED,
        "Goods receipt confirmed and GRN generated.",
    )


@login_required
def invoice_page(request):
    if request.method == "GET":
        request_queryset = selected_supplier_requests(request.user)
        form = InvoiceForm(
            initial={"invoice_number": preview_doc_number(DocumentNumberSetting.DOC_INVOICE, "INV")},
            request_queryset=request_queryset,
            supplier=locked_supplier_for(request.user),
        )
        records = Invoice.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
        return render(request, "procurement/invoice_page.html", {"form": form, "records": records})
    return handle_document_form(
        request,
        InvoiceForm,
        Invoice,
        "procurement/invoice_page.html",
        ProcurementRequest.STATUS_INVOICED,
        "Invoice recorded.",
    )


@login_required
def payment_tracking_page(request):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    request_queryset = selected_supplier_requests(request.user)
    records = PaymentRecord.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
    if request.method == "POST":
        form = PaymentRecordForm(request.POST, request_queryset=request_queryset)
        if form.is_valid():
            payment = form.save()
            payment.request.status = (
                ProcurementRequest.STATUS_PAID
                if payment.status == PaymentRecord.STATUS_PAID
                else ProcurementRequest.STATUS_PAYMENT_PROCESSING
            )
            payment.request.save(update_fields=["status"])
            messages.success(request, "Payment status updated.")
            return redirect("payment_tracking_page")
    else:
        form = PaymentRecordForm(request_queryset=request_queryset)
    return render(request, "procurement/payment_tracking_page.html", {"form": form, "records": records})


@login_required
def receipt_page(request):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    can_issue = role_for(request.user) in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPPLIER}
    if request.method == "POST" and not can_issue:
        return HttpResponseForbidden("Only the selected supplier or admin can issue receipts.")
    request_queryset = selected_supplier_requests(request.user).filter(payment__status=PaymentRecord.STATUS_PAID)
    supplier = locked_supplier_for(request.user)
    records = Receipt.objects.select_related("request", "request__school", "supplier").filter(request__in=visible_requests(request.user))
    if request.method == "POST":
        form = ReceiptForm(request.POST, request.FILES, request_queryset=request_queryset, supplier=supplier)
        if form.is_valid():
            receipt = form.save(commit=False)
            if not hasattr(receipt.request, "payment") or receipt.request.payment.status != PaymentRecord.STATUS_PAID:
                form.add_error("request", "A receipt can only be issued after payment is marked Paid.")
            else:
                receipt.receipt_number = generate_doc_number(DocumentNumberSetting.DOC_RECEIPT, "RCT")
                if supplier:
                    receipt.supplier = supplier
                receipt.save()
                receipt.request.status = ProcurementRequest.STATUS_CLOSED
                receipt.request.save(update_fields=["status"])
                notify_user(receipt.request.created_by, "Receipt issued", f"{receipt.supplier.name} issued receipt {receipt.receipt_number} for {receipt.request.reference}.")
                messages.success(request, "Receipt issued and request closed.")
                return redirect("receipt_page")
    elif can_issue:
        form = ReceiptForm(
            initial={"receipt_number": preview_doc_number(DocumentNumberSetting.DOC_RECEIPT, "RCT")},
            request_queryset=request_queryset,
            supplier=supplier,
        )
    else:
        form = None
    return render(request, "procurement/receipt_page.html", {"form": form, "records": records, "pdf_type": "receipt", "title": "Receipts"})


def handle_document_form(request, form_class, model_class, template, next_status, success_message):
    forbidden = require_editor(request.user)
    if forbidden:
        return forbidden
    records = model_class.objects.select_related("request", "request__school").filter(request__in=visible_requests(request.user))
    request_queryset = selected_supplier_requests(request.user)
    supplier = locked_supplier_for(request.user)
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, request_queryset=request_queryset, supplier=supplier)
        if form.is_valid():
            record = form.save()
            number_fields = {
                PurchaseOrder: ("po_number", DocumentNumberSetting.DOC_PO, "PO"),
                DeliveryNote: ("delivery_number", DocumentNumberSetting.DOC_DELIVERY, "DN"),
                GoodsReceivedNote: ("grn_number", DocumentNumberSetting.DOC_GRN, "GRN"),
                Invoice: ("invoice_number", DocumentNumberSetting.DOC_INVOICE, "INV"),
                Receipt: ("receipt_number", DocumentNumberSetting.DOC_RECEIPT, "RCT"),
            }
            if model_class in number_fields:
                field, doc_type, prefix = number_fields[model_class]
                setattr(record, field, generate_doc_number(doc_type, prefix))
                record.save(update_fields=[field])
            record.request.status = next_status
            record.request.save(update_fields=["status"])
            notify_user(record.request.created_by, success_message, f"{record} was recorded for {record.request.reference}.")
            messages.success(request, success_message)
            return redirect(request.resolver_match.url_name)
    else:
        form = form_class(request_queryset=request_queryset, supplier=supplier)
    return render(request, template, {"form": form, "records": records})


@login_required
def reports_page(request):
    requests = apply_request_filters(visible_requests(request.user), request.GET)
    payments = PaymentRecord.objects.filter(request__in=requests)
    context = {
        "status_counts": requests.values("status").annotate(count=Count("id")).order_by("status"),
        "school_totals": payments.values("request__school__name").annotate(total=Sum("amount")).order_by("-total"),
        "supplier_totals": payments.values("request__selected_supplier__name").annotate(total=Sum("amount")).order_by("-total"),
        "district_totals": payments.values("request__school__district").annotate(total=Sum("amount")).order_by("-total"),
        "category_totals": RequestItem.objects.filter(request__in=requests).values("product__category__name").annotate(total=Sum("quantity")).order_by("product__category__name"),
        "schools": School.objects.all(),
        "suppliers": Supplier.objects.all(),
        "statuses": ProcurementRequest.STATUS_CHOICES,
        "filters": request.GET,
    }
    return render(request, "procurement/reports_page.html", context)


@login_required
def reports_export(request, export_type):
    requests = apply_request_filters(visible_requests(request.user), request.GET)
    payments = PaymentRecord.objects.filter(request__in=requests).select_related("request", "request__school", "request__selected_supplier")
    if export_type == "excel":
        wb = Workbook()
        ws = wb.active
        ws.title = "Payments"
        ws.append(["Reference", "School", "District", "Supplier", "Status", "Amount", "Paid date"])
        for payment in payments:
            ws.append([
                payment.request.reference,
                payment.request.school.name,
                payment.request.school.district,
                payment.request.selected_supplier.name if payment.request.selected_supplier else "",
                payment.get_status_display(),
                float(payment.amount),
                payment.paid_date.isoformat() if payment.paid_date else "",
            ])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="schoolprocure-report.xlsx"'
        wb.save(response)
        return response
    if export_type == "pdf":
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        y = A4[1] - 50
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, "SchoolProcure Report")
        y -= 30
        pdf.setFont("Helvetica", 9)
        for payment in payments:
            line = f"{payment.request.reference} | {payment.request.school.name} | {payment.get_status_display()} | {payment.amount:,.2f}"
            pdf.drawString(50, y, line[:110])
            y -= 16
            if y < 60:
                pdf.showPage()
                y = A4[1] - 50
        pdf.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="schoolprocure-report.pdf"'
        return response
    return HttpResponse(status=404)


@login_required
def approval_update(request, pk):
    step = get_object_or_404(ApprovalStep, pk=pk)
    if role_for(request.user) not in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_VIEWER}:
        return HttpResponseForbidden("Only admin or oversight users can update approvals.")
    if request.method == "POST":
        form = ApprovalStepForm(request.POST, instance=step)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.approved_by = request.user
            approval.decided_at = timezone.now()
            approval.save()
            notify_user(approval.request.created_by, "Approval updated", f"{approval.get_approver_role_display()} marked {approval.request.reference} as {approval.get_status_display()}.")
            messages.success(request, "Approval step updated.")
    return redirect("request_detail", pk=step.request.pk)


@login_required
def document_number_settings(request):
    if role_for(request.user) != UserProfile.ROLE_ADMIN:
        return HttpResponseForbidden("Only admins can manage document numbering.")
    if request.method == "POST":
        form = DocumentNumberSettingForm(request.POST)
        if form.is_valid():
            setting, _ = DocumentNumberSetting.objects.update_or_create(
                document_type=form.cleaned_data["document_type"],
                defaults={
                    "prefix": form.cleaned_data["prefix"],
                    "next_number": form.cleaned_data["next_number"],
                    "padding": form.cleaned_data["padding"],
                },
            )
            messages.success(request, f"{setting.get_document_type_display()} numbering updated.")
            return redirect("document_number_settings")
    else:
        form = DocumentNumberSettingForm()
    return render(request, "procurement/document_number_settings.html", {"form": form, "settings": DocumentNumberSetting.objects.all()})


@login_required
def user_manual_page(request):
    role = role_for(request.user)
    return render(request, "procurement/user_manual.html", {"role": role})


@login_required
def noticeboard_page(request):
    notices = visible_notices(request.user)
    return render(request, "procurement/noticeboard.html", {"notices": notices})


@login_required
def messages_page(request):
    inbox = ClarificationMessage.objects.filter(recipient=request.user).select_related("sender", "request")
    sent = ClarificationMessage.objects.filter(sender=request.user).select_related("recipient", "request")[:10]
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        inbox = inbox.filter(Q(subject__icontains=q) | Q(body__icontains=q) | Q(sender__username__icontains=q))
    if status == "unread":
        inbox = inbox.filter(is_read=False)
    elif status == "read":
        inbox = inbox.filter(is_read=True)
    unread_count = inbox.filter(is_read=False).count()
    return render(request, "procurement/messages_page.html", {"inbox": inbox, "sent": sent, "unread_count": unread_count, "filters": request.GET})


@login_required
def message_detail(request, pk):
    message = get_object_or_404(
        ClarificationMessage.objects.select_related("sender", "recipient", "request"),
        pk=pk,
    )
    if request.user not in {message.sender, message.recipient} and not request.user.is_superuser:
        return HttpResponseForbidden("You can only view messages you sent or received.")
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save(update_fields=["is_read"])
    return render(request, "procurement/message_detail.html", {"message": message})


@login_required
def message_create(request):
    if request.method == "POST":
        form = ClarificationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            notify_user(message.recipient, "New clarification message", f"{request.user.username}: {message.subject}")
            messages.success(request, "Clarification message sent.")
            return redirect("messages_page")
    else:
        form = ClarificationMessageForm()
    return render(request, "procurement/message_form.html", {"form": form})


@login_required
def assistant_ask(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Open the assistant and type a question about using SchoolProcure."})
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    question = (payload.get("message") or request.POST.get("message") or "").lower()
    answers = [
        (("request", "item", "deadline"), "Schools create a procurement request from Requests, add as many items as needed, and set a quotation deadline. Suppliers cannot submit quotations after that deadline."),
        (("quote", "quotation", "supplier"), "Suppliers use Quotations to choose an open request and enter prices. The school then compares quotations and records the reason for selecting the preferred supplier."),
        (("purchase", "po"), "After a quotation is approved, the school uploads or generates the Purchase Order. The selected supplier confirms the PO before preparing goods."),
        (("delivery", "deliver"), "The selected supplier records the delivery note, including delivered items and any shortages. The system tracks the expected delivery date from the approved quotation."),
        (("grn", "received", "goods"), "The school confirms delivered goods on the GRN page. That creates the Goods Received Note and moves the request to GRN Confirmed."),
        (("invoice",), "After the school confirms receipt, the supplier uploads the invoice and amount on the Invoice page."),
        (("payment", "paid"), "The school records payment as Processing or Paid. Once it is Paid, the supplier can issue a receipt."),
        (("receipt",), "Receipts are issued by the supplier only after payment is marked Paid. Issuing the receipt closes the procurement request."),
        (("message", "clarification"), "Use Messages to ask another user for clarification about a request, quotation, document, or payment."),
        (("report", "excel", "pdf"), "Reports show spending and status summaries. Use the export buttons to download PDF or Excel reports."),
    ]
    answer = "I can help with SchoolProcure. Ask about creating requests, adding items, quotation deadlines, approving suppliers, delivery notes, GRNs, invoices, payments, receipts, reports, or messages."
    for keywords, text in answers:
        if any(keyword in question for keyword in keywords):
            answer = text
            break
    return JsonResponse({"answer": answer})


@login_required
def document_pdf(request, document_type, pk):
    mapping = {
        "quotation": (Quotation, "Quotation"),
        "po": (PurchaseOrder, "Purchase Order"),
        "delivery": (DeliveryNote, "Delivery Note"),
        "grn": (GoodsReceivedNote, "Goods Received Note"),
        "invoice": (Invoice, "Invoice"),
        "receipt": (Receipt, "Receipt"),
    }
    if document_type not in mapping:
        return HttpResponse(status=404)
    model, title = mapping[document_type]
    obj = get_object_or_404(model.objects.filter(request__in=visible_requests(request.user)), pk=pk)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    req = obj.request
    margin = 42

    def money(value):
        return f"K {Decimal(value):,.2f}"

    def footer():
        pdf.setStrokeColor(colors.HexColor("#dbe3ee"))
        pdf.line(margin, 38, width - margin, 38)
        pdf.setFillColor(colors.HexColor("#657084"))
        pdf.setFont("Helvetica", 8)
        pdf.drawString(margin, 24, "Generated by SchoolProcure for standard school procurement administration.")
        pdf.drawRightString(width - margin, 24, "Powered by Dreambolt Technology")

    pdf.setFillColor(colors.HexColor("#17324d"))
    pdf.rect(0, height - 104, width, 104, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(margin, height - 48, f"SchoolProcure {title}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, height - 70, "Swift Technologies")
    pdf.drawRightString(width - margin, height - 48, req.reference)
    pdf.drawRightString(width - margin, height - 70, timezone.now().strftime("%d %b %Y"))

    y = height - 135
    pdf.setFillColor(colors.HexColor("#172033"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Document details")
    y -= 18
    pdf.setFont("Helvetica", 9)
    rows = [
        ("Reference", req.reference),
        ("School", req.school.name),
        ("District", req.school.district),
        ("Status", req.get_status_display()),
    ]
    supplier = getattr(obj, "supplier", None) or getattr(req, "selected_supplier", None)
    if supplier:
        rows.append(("Supplier", supplier.name))
    if isinstance(obj, Quotation):
        rows.extend([
            ("Quotation number", obj.quotation_number),
            ("Delivery days", f"{obj.delivery_days} days"),
            ("Valid until", obj.valid_until.strftime("%d %b %Y") if obj.valid_until else "Not specified"),
        ])
    for label, value in rows:
        pdf.setFillColor(colors.HexColor("#657084"))
        pdf.drawString(margin, y, label)
        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.drawString(165, y, str(value))
        y -= 14
    y -= 16

    table_left = margin
    table_right = width - margin
    pdf.setFillColor(colors.HexColor("#eef3f8"))
    pdf.rect(table_left, y - 6, table_right - table_left, 24, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#172033"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(table_left + 8, y, "Item")
    pdf.drawString(245, y, "Qty")
    pdf.drawString(320, y, "Unit price")
    pdf.drawRightString(table_right - 8, y, "Line total")
    y -= 20
    pdf.setFont("Helvetica", 9)
    total = Decimal("0.00")
    quote = obj if isinstance(obj, Quotation) else req.quotations.filter(is_selected=True).first()
    for item in req.items.select_related("product", "product__category"):
        unit_price = Decimal("0.00")
        if quote:
            quote_item = quote.items.filter(request_item=item).first()
            unit_price = quote_item.unit_price if quote_item else Decimal("0.00")
        line_total = item.quantity * unit_price
        total += line_total
        if y < 86:
            footer()
            pdf.showPage()
            y = height - 60
        pdf.setStrokeColor(colors.HexColor("#edf2f7"))
        pdf.line(table_left, y - 5, table_right, y - 5)
        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.drawString(table_left + 8, y, item.product.name[:34])
        pdf.setFillColor(colors.HexColor("#657084"))
        pdf.drawString(245, y, f"{item.quantity:g} {item.product.unit}")
        pdf.drawString(320, y, money(unit_price))
        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.drawRightString(table_right - 8, y, money(line_total))
        y -= 18
    y -= 8
    amount = getattr(obj, "amount", total)
    pdf.setFillColor(colors.HexColor("#17324d"))
    pdf.rect(320, y - 10, table_right - 320, 30, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(330, y, "Total")
    pdf.drawRightString(table_right - 8, y, money(amount))
    footer()
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{document_type}-{pk}.pdf"'
    return response
    DocumentNumberSetting,
    EmailNotification,
