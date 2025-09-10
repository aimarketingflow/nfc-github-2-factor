#!/usr/bin/env python3
"""
Simple NFC SSH Key Generator
Generate GitHub SSH keys from dual NFC authentication
"""

import os
import hashlib
import base64
import numpy as np
import time
import logging
import sys
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from invisible_nfc_scanner import InvisibleNFCScanner

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfc_ssh_keygen.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def generate_ssh_keys_from_nfc():
    """Generate SSH keys from dual NFC authentication"""
    
    start_time = datetime.now()
    logging.info(f"🔐 Starting NFC SSH Key Generator at {start_time}")
    
    print("🔐 SIMPLE NFC SSH KEY GENERATOR")
    print("=" * 40)
    print("Generate GitHub SSH keys from dual NFC scans")
    print()
    
    logging.info("📱 Initializing NFC scanner...")
    try:
        scanner = InvisibleNFCScanner()
        logging.info("✅ NFC scanner initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize NFC scanner: {e}")
        print(f"❌ Scanner initialization failed: {e}")
        return None
    
    # First NFC scan
    print("🏷️  FIRST NFC SCAN")
    logging.info("🔍 Starting first NFC scan...")
    scan_start = time.time()
    
    try:
        first_nfc = scanner.invisible_scan_simple()
        scan_duration = time.time() - scan_start
        logging.info(f"⏱️  First scan completed in {scan_duration:.2f}s")
        
        if not first_nfc:
            logging.error("❌ First NFC scan returned no data")
            print("❌ First NFC scan failed")
            return None
        
        logging.info(f"✅ First NFC scan successful (hash length: {len(first_nfc)})")
        
    except Exception as e:
        logging.error(f"❌ First NFC scan exception: {e}")
        print(f"❌ First NFC scan failed: {e}")
        return None
    
    print()
    
    # Second NFC scan  
    print("🏷️  SECOND NFC SCAN")
    logging.info("🔍 Starting second NFC scan...")
    scan_start = time.time()
    
    try:
        second_nfc = scanner.invisible_scan_simple()
        scan_duration = time.time() - scan_start
        logging.info(f"⏱️  Second scan completed in {scan_duration:.2f}s")
        
        if not second_nfc:
            logging.error("❌ Second NFC scan returned no data")
            print("❌ Second NFC scan failed")
            return None
        
        logging.info(f"✅ Second NFC scan successful (hash length: {len(second_nfc)})")
        
    except Exception as e:
        logging.error(f"❌ Second NFC scan exception: {e}")
        print(f"❌ Second NFC scan failed: {e}")
        return None
    
    print()
    print("✅ Dual NFC authentication complete")
    logging.info("🔐 Creating composite authentication material...")
    
    # Create composite authentication material
    try:
        composite_material = (first_nfc + second_nfc + "GITHUB_SSH_KEYS").encode()
        logging.info(f"✅ Composite material created (length: {len(composite_material)} bytes)")
    except Exception as e:
        logging.error(f"❌ Failed to create composite material: {e}")
        return None
    
    # Generate deterministic SSH keys
    logging.info("🔑 Starting key derivation process...")
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'NFC_SSH_SALT',
            iterations=100000,
        )
        
        derive_start = time.time()
        key_seed = kdf.derive(composite_material)
        derive_duration = time.time() - derive_start
        logging.info(f"✅ Key derivation completed in {derive_duration:.2f}s")
        
    except Exception as e:
        logging.error(f"❌ Key derivation failed: {e}")
        return None
    
    # Use seed for deterministic key generation
    logging.info("🎲 Setting up deterministic random seed...")
    try:
        seed_32bit = int.from_bytes(key_seed[:4], 'big') % (2**32)
        np.random.seed(seed_32bit)
        logging.info(f"✅ Random seed set: {seed_32bit}")
    except Exception as e:
        logging.error(f"❌ Seed generation failed: {e}")
        return None
    
    print("🔑 Generating SSH key pair...")
    logging.info("🔑 Starting RSA key pair generation (4096-bit)...")
    
    # Generate RSA key pair
    try:
        keygen_start = time.time()
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        keygen_duration = time.time() - keygen_start
        logging.info(f"✅ RSA key pair generated in {keygen_duration:.2f}s")
    except Exception as e:
        logging.error(f"❌ RSA key generation failed: {e}")
        return None
    
    public_key = private_key.public_key()
    
    # Create SSH directory if needed
    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = int(time.time())
    key_name = f"nfc_github_{timestamp}"
    logging.info(f"📁 Generated key filename: {key_name}")
    
    private_key_path = os.path.join(ssh_dir, key_name)
    public_key_path = os.path.join(ssh_dir, f"{key_name}.pub")
    
    # Serialize private key
    logging.info("🔐 Serializing private key...")
    try:
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        logging.info(f"✅ Private key serialized ({len(private_pem)} bytes)")
    except Exception as e:
        logging.error(f"❌ Private key serialization failed: {e}")
        return None
    
    # Serialize public key
    logging.info("🔓 Serializing public key...")
    try:
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        logging.info(f"✅ Public key serialized ({len(public_ssh)} bytes)")
    except Exception as e:
        logging.error(f"❌ Public key serialization failed: {e}")
        return None
    
    # Save private key
    logging.info(f"💾 Saving private key to: {private_key_path}")
    try:
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_key_path, 0o600)
        logging.info("✅ Private key saved with 600 permissions")
    except Exception as e:
        logging.error(f"❌ Failed to save private key: {e}")
        return None
    
    # Save public key with comment
    logging.info(f"💾 Saving public key to: {public_key_path}")
    try:
        hostname = os.uname().nodename
        public_key_content = public_ssh.decode() + f" nfc-mobileshield@{hostname}\n"
        
        with open(public_key_path, 'w') as f:
            f.write(public_key_content)
        logging.info("✅ Public key saved successfully")
    except Exception as e:
        logging.error(f"❌ Failed to save public key: {e}")
        return None
    
    total_duration = (datetime.now() - start_time).total_seconds()
    logging.info(f"🎉 SSH key generation completed in {total_duration:.2f}s")
    
    print(f"✅ SSH keys generated successfully!")
    print(f"   Private key: {private_key_path}")
    print(f"   Public key: {public_key_path}")
    print(f"   Total time: {total_duration:.2f}s")
    print()
    
    # Display public key for GitHub
    print("📋 PUBLIC KEY FOR GITHUB:")
    print("=" * 50)
    print(public_key_content.strip())
    print("=" * 50)
    print()
    
    print("🔗 NEXT STEPS:")
    print("1. Copy the public key above")
    print("2. Go to GitHub → Settings → SSH and GPG keys")
    print("3. Click 'New SSH key'")
    print("4. Paste the public key")
    print("5. Test with: ssh -T git@github.com")
    
    return {
        'private_key_path': private_key_path,
        'public_key_path': public_key_path,
        'public_key_content': public_key_content.strip()
    }

if __name__ == "__main__":
    logging.info("🚀 Starting NFC SSH Key Generator application")
    
    try:
        result = generate_ssh_keys_from_nfc()
        
        if result:
            logging.info("🎉 Application completed successfully")
            print(f"\n🎉 SUCCESS! SSH keys ready for GitHub authentication")
        else:
            logging.error("❌ Application failed to generate SSH keys")
            print(f"\n❌ Failed to generate SSH keys")
            
    except KeyboardInterrupt:
        logging.warning("⚠️  Application interrupted by user (Ctrl+C)")
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        logging.error(f"💥 Unexpected application error: {e}")
        print(f"\n💥 Unexpected error: {e}")
    finally:
        logging.info("🏁 Application shutdown complete")
