import hashlib

# admin.py - Stores valid admin keys
VALID_ADMIN_KEYS = [
    hashlib.sha256(b'12345').hexdigest(),
    hashlib.sha256(b'BMXIIADMIN').hexdigest(),
    hashlib.sha256(b'SECURE123').hexdigest()
]