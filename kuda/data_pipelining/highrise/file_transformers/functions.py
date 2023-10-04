from typing import Optional

from cryptography.fernet import Fernet

ENCRYPTION_KEY = "5Zs50S4Cbd909UfP-HT-q0OIsFOV0pniGqEGh2XwEZU="

MONTH_STR_TO_NUM = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def encrypt_string(string: str) -> bytes:
    """
    Encrypts a string using the ENCRYPTION_KEY
    Args:
        string (str): The string to encrypt
    Returns:
        str: The encrypted string
    """
    return Fernet(ENCRYPTION_KEY).encrypt(string.encode("utf-8"))


def decrypt_string(string: str) -> str:
    """
    Decrypts a string using the ENCRYPTION_KEY
    Args:
        string (str): The string to decrypt
    Returns:
        str: The decrypted string
    """
    return Fernet(ENCRYPTION_KEY).decrypt(string.encode("utf-8")).decode()


def parse_int(string: Optional[str]) -> Optional[int]:
    """
    Parses a string into an int
    Args:
        string (str): The string to parse
    Returns:
        int: The parsed int
    """
    if string and string.isnumeric():
        return int(string)
    return None


def parse_float(string: Optional[str]) -> Optional[float]:
    """
    Parses a string into a float
    Args:
        string (str): The string to parse
    Returns:
        float: The parsed float
    """
    if string and string.isdecimal():
        return float(string)
    return None
