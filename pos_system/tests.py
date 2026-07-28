from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import SimpleTestCase, TestCase

from directory.models import Business
from pos_system.models import ZRAConfiguration
from pos_system.services.fiscal import PAYMENT_CODES, calculate_line, next_invoice_number
from pos_system.services.zra_vsdc import VSDCClient, VSDCError


class FiscalCalculationTests(SimpleTestCase):
    def test_standard_vat_is_extracted_from_tax_inclusive_price(self):
        product = SimpleNamespace(price=Decimal('116.00'), zra_tax_category='A')

        line = calculate_line(product, 2)

        self.assertEqual(line['gross'], Decimal('232.00'))
        self.assertEqual(line['taxable'], Decimal('200.00'))
        self.assertEqual(line['tax'], Decimal('32.00'))
        self.assertEqual(line['rate'], Decimal('16'))

    def test_zero_rate_does_not_add_tax(self):
        product = SimpleNamespace(price=Decimal('75.50'), zra_tax_category='C3')

        line = calculate_line(product, 2)

        self.assertEqual(line['gross'], Decimal('151.00'))
        self.assertEqual(line['taxable'], Decimal('151.00'))
        self.assertEqual(line['tax'], Decimal('0.00'))

    def test_swiftfind_payments_map_to_official_zra_codes(self):
        self.assertEqual(PAYMENT_CODES['cash'], '01')
        self.assertEqual(PAYMENT_CODES['card'], '05')
        self.assertEqual(PAYMENT_CODES['mobile_money'], '06')
        self.assertEqual(PAYMENT_CODES['bank_transfer'], '08')


class VSDCClientTests(SimpleTestCase):
    def setUp(self):
        configuration = SimpleNamespace(
            vsdc_base_url='http://127.0.0.1:8080/',
            request_timeout_seconds=12,
        )
        self.client = VSDCClient(configuration)

    @patch('pos_system.services.zra_vsdc.requests.post')
    def test_successful_response_is_returned(self, post):
        response = Mock()
        response.json.return_value = {'resultCd': '000', 'data': {'rcptNo': 7}}
        post.return_value = response

        result = self.client.save_sale({'tpin': '1234567890'})

        self.assertEqual(result['data']['rcptNo'], 7)
        post.assert_called_once_with(
            'http://127.0.0.1:8080/trnsSales/saveSales',
            json={'tpin': '1234567890'},
            timeout=12,
            headers={'Accept': 'application/json'},
        )

    @patch('pos_system.services.zra_vsdc.requests.post')
    def test_zra_rejection_raises_and_does_not_look_successful(self, post):
        response = Mock()
        response.json.return_value = {'resultCd': '884', 'resultMsg': 'Invalid customer TPIN'}
        post.return_value = response

        with self.assertRaisesMessage(VSDCError, 'Invalid customer TPIN'):
            self.client.save_sale({})


class FiscalSequenceAndConfigurationTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(username='owner')
        self.business = Business.objects.create(
            owner=owner,
            name='Test Business',
            description='Test',
            address='Lusaka',
            phone_number='+260970000000',
        )

    def test_invoice_counter_is_uninterrupted_per_invoice_type(self):
        with transaction.atomic():
            first = next_invoice_number(self.business)
        with transaction.atomic():
            second = next_invoice_number(self.business)
        with transaction.atomic():
            training = next_invoice_number(self.business, invoice_type='TRAINING')

        self.assertEqual((first, second, training), (1, 2, 1))

    def test_enabled_configuration_requires_certification_fields(self):
        configuration = ZRAConfiguration(
            business=self.business,
            enabled=True,
            tpin='1234567890',
            branch_id='000',
        )

        with self.assertRaises(ValidationError) as error:
            configuration.full_clean()

        self.assertIn('cis_number', error.exception.message_dict)
        self.assertIn('vsdc_base_url', error.exception.message_dict)
        self.assertIn('device_initialized', error.exception.message_dict)

# Create your tests here.
