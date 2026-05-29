import hmac
import hashlib
import time

def generate_signature(secret, payload):
    return hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

def get_timestamp():
    return str(int(time.time() * 1000))