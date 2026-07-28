# Swiftfind ZRA Smart Invoice setup

Swiftfind contains a ZRA-ready fiscal layer, but ZRA Smart Invoice mode is deliberately
disabled by default. It must only be enabled after the business has been approved,
its CIS/device has been initialized, and its VSDC service is reachable.

The API contract implemented here follows the ZRA VSDC API Specification v1.0.8.
ZRA certification and production access remain external prerequisites.

## Safety behaviour

- Existing businesses continue to issue standard Swiftfind receipts.
- A standard receipt is explicitly marked **not a ZRA Smart Invoice**.
- A ZRA-enabled sale is rejected if configuration, product classification, stock,
  TPIN validation, or VSDC certification fails.
- Stock is locked and revalidated inside a database transaction.
- The browser cannot choose the tax amount or product price.
- Certified sales and their fiscal event journal cannot be deleted in Django admin.
- If ZRA certifies the invoice but the stock sync fails, the invoice is preserved and
  marked `FAILED` for stock retry/reconciliation.
- API keys are not stored by Swiftfind; they remain in the ZRA VSDC installation.

## Activation order

1. Obtain the business TPIN, ZRA-approved CIS number, branch ID and VSDC package/access.
2. Install and initialize the official VSDC according to ZRA's instructions.
3. In Django admin, create **POS system > ZRA configurations** for the business.
4. Enter the TPIN, three-digit branch ID, CIS number, VSDC base URL and currency.
5. Leave `enabled` off, mark `device_initialized` only after successful initialization,
   and save.
6. Synchronize ZRA standard codes and choose a level-4 UNSPSC classification for every
   product. The current release stores the selected codes; code-list synchronization
   remains part of the VSDC onboarding procedure.
7. Complete each product's ZRA fields, then select products in Django admin and run
   **Register/update selected products with ZRA VSDC**.
8. Confirm every sellable product shows `zra_registered = true`.
9. Test sales against ZRA's sandbox and reconcile the VSDC responses.
10. After ZRA certification, switch the configuration to production and enable it.

## PythonAnywhere deployment

Run from a PythonAnywhere Bash console:

```bash
cd /home/Dreambolt/swiftfind
cp db.sqlite3 "db.sqlite3.pre-zra-$(date +%Y%m%d-%H%M%S).bak"
git fetch origin
git pull --ff-only origin master
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py check
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py migrate --plan
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py migrate --noinput
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py collectstatic --noinput
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py test pos_system.tests
```

Then open the PythonAnywhere **Web** tab for `www.dbt.africa`, press **Reload**, and
verify:

- `/swiftfind/pos1/`
- a standard test receipt while ZRA mode is disabled
- Django admin ZRA configuration and product fields
- sandbox VSDC product registration before enabling fiscal sales

No new environment variable is required. `vsdc_base_url`, TPIN, branch and CIS number
are per-business database configuration. Do not add or store a ZRA API key in Django;
VSDC is responsible for ZRA credentials.

## Rollback

If application code fails before enabling ZRA mode:

```bash
cd /home/Dreambolt/swiftfind
git log --oneline -5
git switch --detach <PREVIOUS_GOOD_COMMIT>
/home/Dreambolt/dream-bolt-technologies/.venv/bin/python manage.py check
```

Reload the web app. The migration only adds nullable/defaulted tables and columns, so
the previous code can continue using the database. Do not reverse the migration after
real fiscal data exists.

If migration itself fails before any fiscal sale, restore the backup:

```bash
cd /home/Dreambolt/swiftfind
cp db.sqlite3.pre-zra-YYYYMMDD-HHMMSS.bak db.sqlite3
```

If an invoice has already been certified, never delete or renumber it. Restore the
application code only, retain the database and VSDC records, and reconcile the invoice
with ZRA before resuming sales.
