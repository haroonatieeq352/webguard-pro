import hashlib
import hmac
from django.conf import settings
import requests

def is_easypaisa_mock_mode():
    """
    Checks if EasyPaisa is configured in mock mode (using placeholder or empty keys).
    """
    return (
        not settings.EASYPAISA_STORE_ID
        or "your-" in settings.EASYPAISA_STORE_ID
        or not settings.EASYPAISA_HASH_KEY
        or "your-" in settings.EASYPAISA_HASH_KEY
    )

def generate_easypaisa_hash(param_str: str, hash_key: str) -> str:
    """
    Generates an HMAC SHA-256 or AES signature for EasyPaisa API requests.
    Typically, EasyPaisa uses HMAC-SHA256 with hash_key.
    """
    key_bytes = hash_key.encode('utf-8')
    data_bytes = param_str.encode('utf-8')
    return hmac.new(key_bytes, data_bytes, hashlib.sha256).hexdigest()

def initiate_easypaisa_wallet_payment(order_id: str, amount_pkr: float, mobile_no: str, email: str):
    """
    Initiates an EasyPaisa Wallet payment (Mobile Account Payment).
    If in mock mode, it returns a simulated successful initiation dictionary.
    """
    amount_str = f"{amount_pkr:.2f}"
    
    if is_easypaisa_mock_mode():
        # Simulated response from EasyPaisa
        return {
            'responseCode': '0000',
            'responseDesc': 'SUCCESS',
            'transactionId': f"EP-MOCK-{order_id}",
            'orderId': order_id,
            'amount': amount_str,
            'is_mock': True
        }
        
    # Real Integration API Call
    # Format: orderId=123&amount=10.00&postBackURL=...
    # We sign parameters using the hash key.
    # In sandbox/production, we send a POST request to EASYPAISA_API_URL.
    url = settings.EASYPAISA_API_URL
    payload = {
        'storeId': settings.EASYPAISA_STORE_ID,
        'orderId': order_id,
        'transactionAmount': amount_str,
        'mobileNum': mobile_no,
        'emailAddress': email,
        'transactionType': 'MA', # MA = Mobile Account
    }
    
    # Generate signature
    # Typically ordered key-value string:
    param_str = f"amount={amount_str}&emailAddress={email}&mobileNum={mobile_no}&orderId={order_id}&storeId={settings.EASYPAISA_STORE_ID}&transactionType=MA"
    payload['signature'] = generate_easypaisa_hash(param_str, settings.EASYPAISA_HASH_KEY)
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        return {
            'responseCode': '9999',
            'responseDesc': f"HTTP Request failed: {str(e)}",
            'is_error': True
        }
