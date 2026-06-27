# SchoolProcure

SchoolProcure is a Django 5 school procurement management system. Schools create procurement requests, suppliers submit quotations and deliver goods, schools upload or generate Purchase Orders, confirm receipt with Goods Received Notes, record invoices, and track payment as Processing or Paid through normal government procedures.

The application uses procurement workflow statuses throughout.

## Features

- Role-based login for Admin, School user, Supplier user, and Ministry/DEBS/PEO viewer
- Schools, suppliers, product categories, and product catalogue
- Procurement request creation with multiple request items
- Supplier quotations and quotation comparison
- Purchase Order upload/generation, supplier confirmation, delivery notes, GRNs, invoices, and payment tracking
- Dashboard metrics and reports by school, supplier, district, and category
- Noticeboard for school, supplier, and oversight announcements
- Internal clarification messages between users, optionally linked to procurement requests
- User manual pages for schools and suppliers
- Search and filtering for requests, suppliers, products, reports, and messages
- Approval steps for Head teacher, Procurement committee, and DEBS/PEO review
- PDF and Excel report exports
- Configurable document numbering for PO, Delivery Note, GRN, and Invoice numbers
- Email notification hooks for key workflow events
- PDF generation for quotation, PO, delivery note, GRN, and invoice
- SQLite development database
- Bootstrap 5 responsive UI
- Django admin configuration
- Demo data seeding

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo logins:

- `admin` / `12345678`
- `school` / `12345678`
- `supplier` / `12345678`
- `viewer` / `Viewer123!`

## GitHub deployment preparation

```bash
git init
git add .
git commit -m "Initial SchoolProcure Django app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/SchoolProcure.git
git push -u origin main
```

Before public deployment, set a production `SECRET_KEY`, set `DEBUG = False`, and restrict `ALLOWED_HOSTS` to your domain.

Useful production environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=yourdomain.com,yourusername.pythonanywhere.com`
- `DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `DJANGO_DEFAULT_FROM_EMAIL=procurement@yourdomain.com`
- SMTP settings can be added in `schoolprocure/settings.py` for the email provider you choose.

## PythonAnywhere deployment

The current GitHub branch for this app is:

```text
https://github.com/eddiemac1993/swiftfind/tree/schoolprocure
```

1. Create a new PythonAnywhere web app using manual configuration and a supported Python version.
2. Clone the deployment branch:

   ```bash
   cd ~
   git clone --branch schoolprocure https://github.com/eddiemac1993/swiftfind.git SchoolProcure
   cd SchoolProcure
   bash pythonanywhere_setup.sh
   ```

3. In the PythonAnywhere Web tab, set the virtualenv path to `/home/YOUR_PYTHONANYWHERE_USERNAME/SchoolProcure/.venv`.
4. Replace the WSGI file contents with `pythonanywhere_wsgi.py`, updating `YOUR_PYTHONANYWHERE_USERNAME`.
5. Add static files mapping:

   - URL: `/static/`
   - Directory: `/home/YOUR_PYTHONANYWHERE_USERNAME/SchoolProcure/staticfiles`

6. Add media files mapping if uploads are used:

   - URL: `/media/`
   - Directory: `/home/YOUR_PYTHONANYWHERE_USERNAME/SchoolProcure/media`

7. Reload the web app.
