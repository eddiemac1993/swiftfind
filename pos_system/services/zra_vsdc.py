import requests


class VSDCError(RuntimeError):
    pass


class VSDCClient:
    """Small, auditable client for the ZRA VSDC REST service."""

    def __init__(self, configuration):
        self.configuration = configuration
        self.base_url = configuration.vsdc_base_url.rstrip('/')
        self.timeout = configuration.request_timeout_seconds

    def post(self, endpoint, payload):
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=self.timeout,
                headers={'Accept': 'application/json'},
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise VSDCError(f"VSDC communication failed: {exc}") from exc

        if str(body.get('resultCd')) != '000':
            raise VSDCError(
                f"VSDC rejected the request ({body.get('resultCd', 'unknown')}): "
                f"{body.get('resultMsg', 'No response message')}"
            )
        return body

    def save_sale(self, payload):
        return self.post('/trnsSales/saveSales', payload)

    def save_item(self, payload):
        return self.post('/items/saveItem', payload)

    def update_item(self, payload):
        return self.post('/items/updateItem', payload)

    def save_stock_items(self, payload):
        return self.post('/stock/saveStockItems', payload)

    def save_stock_master(self, payload):
        return self.post('/stockMaster/saveStockMaster', payload)
