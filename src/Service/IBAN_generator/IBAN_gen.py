import random
from datetime import datetime
from schwifty import IBAN

"""
This service is for generating polish IBANs
"""

bank_codes = [
    "101", "102", "103", "104", "105", "106", "107", "108", "109",
    "114", "116", "124", "132", "144", "154", "158", "161", "168",
    "175", "184", "187", "189", "191", "193", "194", "203", "212",
    "213", "214", "215", "216", "219", "224", "229", "235", "237",
    "243", "247", "249", "251", "280", "283", "285", "291"
]


def generate_random_digits(length):
    """Generate random digits of given length"""
    return ''.join(random.choices("0123456789", k=length))


def generate_iban(use_timestamp=True):
    """
    Generates polish IBAN number using shwifty library

    Args:
        use_timestamp (bool): Flag to determine
        whether current time should be used to decrease chance of repeated number

    Returns:
        str: IBAN number with country code
    """
    bank_code = random.choice(bank_codes)

    if use_timestamp:
        timestamp = datetime.now().strftime(
            "%y%m%d%H%M%S")
        account_number = timestamp + generate_random_digits(16 - len(timestamp))
    else:
        account_number = generate_random_digits(16)

    try:
        iban = IBAN.generate('PL', bank_code, account_number)
        return str(iban[2:])
    except ValueError as e:
        return {"error": str(e)}
