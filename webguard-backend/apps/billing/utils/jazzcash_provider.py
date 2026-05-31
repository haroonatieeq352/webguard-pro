import hashlib
import hmac
from django.conf import settings

def is_jazzcash_mock_mode():
    """
    Checks if JazzCash is configured in mock mode (using placeholder or empty keys).
    """
    return (
        not settings.JAZZCASH_MERCHANT_ID
        or "your-" in settings.JAZZCASH_MERCHANT_ID
        or not settings.JAZZCASH_INTEGRITY_SALT
        or "your-" in settings.JAZZCASH_INTEGRITY_SALT
    )

def generate_jazzcash_hash(params: dict, secure_key: str) -> str:
    """
    Calculates the SHA-256 hash checksum for JazzCash parameters.
    Standard JazzCash V2.0 / V1.1 hash:
    1. Sort parameters alphabetically by key.
    2. Exclude empty/null values and the secure hash itself.
    3. Prepend the secure key (salt) and join values with '&'.
    4. Compute SHA-256 hash.
    """
    sorted_keys = sorted(params.keys())
    sorted_values = []
    
    for key in sorted_keys:
        val = params[key]
        if val != "" and val is not None and key != "pp_SecureHash":
            # Convert to string and strip
            sorted_values.append(str(val).strip())
            
    hash_string = secure_key + "&" + "&".join(sorted_values)
    return hashlib.sha256(hash_string.encode('utf-8')).hexdigest().upper()

def verify_jazzcash_hash(params: dict, secure_key: str) -> bool:
    """
    Verifies a received JazzCash callback signature.
    """
    received_hash = params.get('pp_SecureHash')
    if not received_hash:
        return False
    calculated_hash = generate_jazzcash_hash(params, secure_key)
    return hmac.compare_digest(received_hash.upper(), calculated_hash.upper())

def prepare_jazzcash_payment_fields(txn_ref_no: str, amount_pkr: float, description: str, return_url: str, user_id: str, tier: str) -> dict:
    """
    Prepares standard JazzCash checkout payload fields.
    """
    from django.utils import timezone
    now = timezone.now()
    txn_date_str = now.strftime("%Y%m%d%H%M%S")
    expiry_date_str = (now + timezone.timedelta(hours=2)).strftime("%Y%m%d%H%M%S")
    
    # Amount needs to be formatted in minor units (cents / paisas)
    # E.g., Rs. 100.00 is represented as 10000 (100 * 100)
    amount_minor = int(amount_pkr * 100)
    
    fields = {
        'pp_Version': '1.1',
        'pp_TxnType': 'MWALLET',
        'pp_Language': 'EN',
        'pp_MerchantID': settings.JAZZCASH_MERCHANT_ID,
        'pp_SubMerchantID': '',
        'pp_Password': settings.JAZZCASH_PASSWORD,
        'pp_TxnRefNo': txn_ref_no,
        'pp_Amount': str(amount_minor),
        'pp_TxnCurrency': 'PKR',
        'pp_TxnDateTime': txn_date_str,
        'pp_BillReference': 'INV_' + txn_ref_no,
        'pp_Description': description[:100],
        'pp_TxnExpiryDateTime': expiry_date_str,
        'pp_ReturnURL': return_url,
        'ppmpf_1': str(user_id),
        'ppmpf_2': str(tier),
        'ppmpf_3': '',
        'ppmpf_4': '',
        'ppmpf_5': '',
    }
    
    # Calculate secure hash
    fields['pp_SecureHash'] = generate_jazzcash_hash(fields, settings.JAZZCASH_INTEGRITY_SALT)
    return fields
