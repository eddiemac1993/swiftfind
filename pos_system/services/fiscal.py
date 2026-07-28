from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from pos_system.models import FiscalEvent, FiscalInvoiceSequence


MONEY = Decimal('0.01')
FOUR_PLACES = Decimal('0.0001')
TAX_RATES = {
    'A': Decimal('16'), 'B': Decimal('16'), 'C1': Decimal('0'),
    'C2': Decimal('0'), 'C3': Decimal('0'), 'D': Decimal('0'),
    'RVAT': Decimal('16'), 'E': Decimal('0'), 'F': Decimal('10'),
    'IPL1': Decimal('5'), 'IPL2': Decimal('0'), 'TL': Decimal('1.5'),
    'ECM': Decimal('5'), 'EXEEG': Decimal('3'), 'TOT': Decimal('0'),
}
PAYMENT_CODES = {
    'cash': '01',
    'card': '05',
    'mobile_money': '06',
    'bank_transfer': '08',
}
TAX_SUFFIXES = {
    'A': 'A', 'B': 'B', 'C1': 'C1', 'C2': 'C2', 'C3': 'C3',
    'D': 'D', 'RVAT': 'Rvat', 'E': 'E', 'F': 'F', 'IPL1': 'Ipl1',
    'IPL2': 'Ipl2', 'TL': 'Tl', 'ECM': 'Ecm', 'EXEEG': 'Exeeg',
    'TOT': 'Tot',
}


def qmoney(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def qfour(value):
    return Decimal(value).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


def calculate_line(product, quantity):
    """ZRA product prices are tax-inclusive."""
    quantity = Decimal(quantity)
    gross = qmoney(product.price * quantity)
    rate = TAX_RATES[product.zra_tax_category]
    divisor = Decimal('1') + (rate / Decimal('100'))
    taxable = qmoney(gross / divisor) if rate else gross
    tax = qmoney(gross - taxable)
    return {
        'gross': gross,
        'taxable': taxable,
        'tax': tax,
        'rate': rate,
    }


def validate_fiscal_products(products):
    errors = []
    for product in products:
        missing = [
            label for label, value in (
                ('ZRA item code', product.zra_item_code),
                ('ZRA item class code', product.zra_item_class_code),
                ('package unit', product.zra_package_unit_code),
                ('quantity unit', product.zra_quantity_unit_code),
            ) if not value
        ]
        if missing or not product.zra_registered:
            detail = ', '.join(missing) if missing else 'VSDC item registration'
            errors.append(f"{product.name}: {detail} is required")
    if errors:
        raise ValidationError(
            "Smart Invoice cannot be issued until these products are configured: "
            + '; '.join(errors)
        )


def build_item_payload(product, configuration, user):
    user_name = user.get_full_name() or user.username
    user_id = str(user.pk)
    category = product.zra_tax_category
    return {
        'tpin': configuration.tpin,
        'bhfId': configuration.branch_id,
        'itemCd': product.zra_item_code,
        'itemClsCd': product.zra_item_class_code,
        'itemTyCd': product.zra_item_type,
        'itemNm': product.name,
        'itemStdNm': product.name,
        'orgnNatCd': product.zra_origin_country_code,
        'pkgUnitCd': product.zra_package_unit_code,
        'qtyUnitCd': product.zra_quantity_unit_code,
        'vatCatCd': category if category not in ('IPL1', 'IPL2', 'TL', 'ECM', 'EXEEG') else None,
        'iplCatCd': category if category in ('IPL1', 'IPL2') else None,
        'tlCatCd': category if category == 'TL' else None,
        'exciseTxCatCd': category if category in ('ECM', 'EXEEG') else None,
        'btchNo': None,
        'bcd': product.barcode or None,
        'dftPrc': float(product.price),
        'addInfo': (product.description or '')[:100] or None,
        'sftyQty': 0,
        'svcChargeYn': 'Y' if category == 'F' else 'N',
        'rentalYn': 'N',
        'useYn': 'Y' if product.is_active else 'N',
        'regrNm': user_name,
        'regrId': user_id,
        'modrNm': user_name,
        'modrId': user_id,
    }


def next_invoice_number(business, invoice_type='NORMAL', transaction_type='SALE'):
    sequence, _ = FiscalInvoiceSequence.objects.get_or_create(
        business=business,
        invoice_type=invoice_type,
        transaction_type=transaction_type,
    )
    sequence = FiscalInvoiceSequence.objects.select_for_update().get(pk=sequence.pk)
    FiscalInvoiceSequence.objects.filter(pk=sequence.pk).update(
        last_number=F('last_number') + 1,
        updated_at=timezone.now(),
    )
    sequence.refresh_from_db(fields=('last_number',))
    return sequence.last_number


def build_sale_payload(sale, configuration):
    issued_at = sale.created_at or timezone.now()
    totals = defaultdict(lambda: Decimal('0'))
    item_list = []

    for index, item in enumerate(sale.pos_system_items.all(), start=1):
        category = item.tax_category_snapshot
        is_ipl = category in ('IPL1', 'IPL2')
        is_tourism = category == 'TL'
        is_excise = category in ('ECM', 'EXEEG')
        is_vat = not (is_ipl or is_tourism or is_excise)
        totals[f'taxable:{category}'] += item.taxable_amount
        totals[f'tax:{category}'] += item.tax_amount
        item_list.append({
            'itemSeq': index,
            'itemCd': item.item_code_snapshot,
            'itemClsCd': item.item_class_code_snapshot,
            'itemNm': item.item_name_snapshot,
            'bcd': item.product.barcode or '' if item.product else '',
            'pkgUnitCd': item.package_unit_code_snapshot,
            'pkg': float(item.quantity),
            'qtyUnitCd': item.quantity_unit_code_snapshot,
            'qty': float(item.quantity),
            'prc': float(item.unit_price),
            'splyAmt': float(item.total_price),
            'dcRt': 0.0,
            'dcAmt': float(item.discount_amount),
            'isrccCd': '',
            'isrccNm': '',
            'isrcRt': 0.0,
            'isrcAmt': 0.0,
            'vatCatCd': category if is_vat else None,
            'exciseTxCatCd': category if is_excise else None,
            'tlCatCd': category if is_tourism else None,
            'iplCatCd': category if is_ipl else None,
            'vatTaxblAmt': float(item.taxable_amount) if is_vat else 0.0,
            'vatAmt': float(item.tax_amount) if is_vat else 0.0,
            'exciseTaxblAmt': float(item.taxable_amount) if is_excise else 0.0,
            'tlTaxblAmt': float(item.taxable_amount) if is_tourism else 0.0,
            'iplTaxblAmt': float(item.taxable_amount) if is_ipl else 0.0,
            'iplAmt': float(item.tax_amount) if is_ipl else 0.0,
            'tlAmt': float(item.tax_amount) if is_tourism else 0.0,
            'exciseTxAmt': float(item.tax_amount) if is_excise else 0.0,
            'totAmt': float(item.total_price),
        })

    payload = {
        'tpin': configuration.tpin,
        'bhfId': configuration.branch_id,
        'orgInvcNo': sale.original_sale.zra_receipt_number if sale.original_sale else 0,
        'cisInvcNo': (
            f"{sale.fiscal_label}-{configuration.cis_number}-"
            f"{sale.cis_invoice_number}"
        ),
        'custTpin': sale.customer_tpin or None,
        'custNm': sale.customer_name_snapshot or 'Walk-In Customer',
        'salesTyCd': {'SALE': 'N', 'CREDIT_NOTE': 'R', 'DEBIT_NOTE': 'D'}[sale.transaction_type],
        'rcptTyCd': {'SALE': 'S', 'CREDIT_NOTE': 'R', 'DEBIT_NOTE': 'D'}[sale.transaction_type],
        'pmtTyCd': PAYMENT_CODES[sale.payment_method],
        'salesSttsCd': '02',
        'cfmDt': issued_at.strftime('%Y%m%d%H%M%S'),
        'salesDt': issued_at.strftime('%Y%m%d'),
        'stockRlsDt': issued_at.strftime('%Y%m%d%H%M%S'),
        'cnclReqDt': None, 'cnclDt': None, 'rfdDt': None, 'rfdRsnCd': '',
        'totItemCnt': len(item_list),
        'totTaxblAmt': float(sum((i.taxable_amount for i in sale.pos_system_items.all()), Decimal('0'))),
        'totTaxAmt': float(sale.tax),
        'taxAmtC': 0.0,
        'tlAmt': float(qfour(totals['tax:TL'])),
        'cashDcRt': 0.0,
        'cashDcAmt': float(sale.discount),
        'totAmt': float(sale.total),
        'prchrAcptcYn': 'N',
        'remark': sale.notes or '',
        'regrId': str(sale.created_by_id or 'system'),
        'regrNm': sale.created_by.get_full_name() or sale.created_by.username if sale.created_by else 'system',
        'modrId': str(sale.created_by_id or 'system'),
        'modrNm': sale.created_by.get_full_name() or sale.created_by.username if sale.created_by else 'system',
        'saleCtyCd': '1',
        'lpoNumber': None,
        'currencyTyCd': sale.currency_code,
        'exchangeRt': str(sale.exchange_rate),
        'destnCountryCd': '',
        'dbtRsnCd': '',
        'invcAdjustReason': '',
        'itemList': item_list,
    }
    for category, suffix in TAX_SUFFIXES.items():
        payload[f'taxblAmt{suffix}'] = float(qfour(totals[f'taxable:{category}']))
        payload[f'taxRt{suffix}'] = float(TAX_RATES[category])
        payload[f'taxAmt{suffix}'] = float(qfour(totals[f'tax:{category}']))
    return payload


def apply_vsdc_response(sale, response):
    data = response.get('data') or {}
    published = data.get('vsdcRcptPbctDate')
    sale.zra_receipt_number = str(data.get('rcptNo', ''))
    sale.zra_internal_data = data.get('intrlData', '')
    sale.zra_receipt_signature = data.get('rcptSign', '')
    sale.zra_sdc_id = data.get('sdcId', '')
    sale.zra_machine_registration_number = data.get('mrcNo', '')
    sale.zra_qr_code_url = data.get('qrCodeUrl', '')
    if published:
        parsed = parse_datetime(published)
        if not parsed:
            try:
                parsed = timezone.datetime.strptime(published, '%Y%m%d%H%M%S')
            except (TypeError, ValueError):
                parsed = None
        if parsed:
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed)
            sale.zra_publication_datetime = parsed
    sale.zra_response = response
    sale.fiscal_status = 'CERTIFIED'
    sale.fiscalized_at = timezone.now()
    sale.save()
    FiscalEvent.objects.create(
        sale=sale, event_type='CERTIFIED',
        message='Invoice certified by ZRA VSDC.', payload=response,
    )


def build_stock_payloads(sale, configuration):
    user_name = (
        sale.created_by.get_full_name() or sale.created_by.username
        if sale.created_by else 'system'
    )
    user_id = str(sale.created_by_id or 'system')
    items = list(sale.pos_system_items.select_related('product'))
    stock_items = []
    stock_master = []
    for index, item in enumerate(items, start=1):
        product = item.product
        category = item.tax_category_snapshot
        is_ipl = category in ('IPL1', 'IPL2')
        is_tourism = category == 'TL'
        is_excise = category in ('ECM', 'EXEEG')
        stock_items.append({
            'itemSeq': index,
            'itemCd': item.item_code_snapshot,
            'itemClsCd': item.item_class_code_snapshot,
            'itemNm': item.item_name_snapshot,
            'pkgUnitCd': item.package_unit_code_snapshot,
            'qtyUnitCd': item.quantity_unit_code_snapshot,
            'qty': float(item.quantity),
            'prc': float(item.unit_price),
            'splyAmt': float(item.total_price),
            'taxblAmt': float(item.taxable_amount),
            'vatCatCd': category if not (is_ipl or is_tourism or is_excise) else None,
            'iplCatCd': category if is_ipl else None,
            'tlCatCd': category if is_tourism else None,
            'exciseTxCatCd': category if is_excise else None,
            'taxAmt': float(item.tax_amount) if not (is_ipl or is_tourism or is_excise) else 0.0,
            'iplAmt': float(item.tax_amount) if is_ipl else 0.0,
            'tlAmt': float(item.tax_amount) if is_tourism else 0.0,
            'exciseTxAmt': float(item.tax_amount) if is_excise else 0.0,
            'totAmt': float(item.total_price),
        })
        stock_master.append({
            'itemCd': item.item_code_snapshot,
            'rsdQty': float(product.stock_quantity),
        })
    movement = {
        'tpin': configuration.tpin,
        'bhfId': configuration.branch_id,
        'sarNo': sale.cis_invoice_number,
        'orgSarNo': 0,
        'regTyCd': 'M',
        'custTpin': sale.customer_tpin or None,
        'custNm': sale.customer_name_snapshot or None,
        'custBhfId': None,
        'sarTyCd': '02',
        'ocrnDt': sale.created_at.strftime('%Y%m%d'),
        'totItemCnt': len(items),
        'totTaxblAmt': float(sum((i.taxable_amount for i in items), Decimal('0'))),
        'totTaxAmt': float(sale.tax),
        'totAmt': float(sale.total),
        'remark': sale.notes or None,
        'regrId': user_id, 'regrNm': user_name,
        'modrId': user_id, 'modrNm': user_name,
        'itemList': stock_items,
    }
    master = {
        'tpin': configuration.tpin,
        'bhfId': configuration.branch_id,
        'regrId': user_id, 'regrNm': user_name,
        'modrId': user_id, 'modrNm': user_name,
        'stockItemList': stock_master,
    }
    return movement, master
