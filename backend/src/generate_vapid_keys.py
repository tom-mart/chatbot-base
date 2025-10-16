#!/usr/bin/env python3
"""
Generate VAPID keys for push notifications.
Run this once to generate keys and add them to your .env file.
"""
from pywebpush import webpush
import base64
import os

def generate_vapid_keys():
    """Generate VAPID key pair"""
    # Generate private key
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get private key in raw format
    private_key_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).strip(b'=').decode('utf-8')
    
    # Get public key in raw format
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).strip(b'=').decode('utf-8')
    
    return private_key_b64, public_key_b64

if __name__ == '__main__':
    print("Generating VAPID keys...")
    private_key, public_key = generate_vapid_keys()
    
    print("\n" + "="*80)
    print("VAPID Keys Generated Successfully!")
    print("="*80)
    print("\nAdd these to your .env file:\n")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_SUBJECT=mailto:admin@chatbot.app")
    print("\n" + "="*80)
    
    # Also save to a file
    env_file = os.path.join(os.path.dirname(__file__), '.env.vapid')
    with open(env_file, 'w') as f:
        f.write(f"VAPID_PRIVATE_KEY={private_key}\n")
        f.write(f"VAPID_PUBLIC_KEY={public_key}\n")
        f.write(f"VAPID_SUBJECT=mailto:admin@chatbot.app\n")
    
    print(f"\nKeys also saved to: {env_file}")
    print("Copy these values to your main .env file")
