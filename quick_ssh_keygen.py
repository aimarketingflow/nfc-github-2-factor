#!/usr/bin/env python3
"""
Quick SSH Key Generator using existing USB authentication pack
Uses stored NFC hash instead of rescanning to avoid mismatch issues
"""

import json
import hashlib
import logging
import os
import subprocess
import sys
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def find_usb_drive():
    """Find the USB drive with authentication pack"""
    
    usb_paths = ['/Volumes/YOUR_USB_DRIVE', '/Volumes/SILVER', '/Volumes/USB', '/Volumes/Untitled']
    
    for path in usb_paths:
        if os.path.exists(path):
            auth_pack_path = os.path.join(path, 'mobileshield_auth_pack.json')
            if os.path.exists(auth_pack_path):
                logging.info(f"✅ Found USB with auth pack: {path}")
                return path
    
    logging.error("❌ No USB drive with auth pack found")
    return None

def load_auth_pack(usb_path):
    """Load and verify authentication pack"""
    
    auth_pack_path = os.path.join(usb_path, 'mobileshield_auth_pack.json')
    
    try:
        with open(auth_pack_path, 'r') as f:
            pack_data = json.load(f)
        
        logging.info("✅ Auth pack loaded successfully")
        
        # Load ambient audio file
        audio_info = pack_data['stored_files']['ambient_audio_file']
        audio_path = audio_info['file_path']
        
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            logging.info(f"✅ Audio file loaded: {len(audio_data)} bytes")
        else:
            logging.error(f"❌ Audio file not found: {audio_path}")
            return None, None
        
        # Load EMF file
        emf_info = pack_data['stored_files']['emf_data_file']
        emf_path = emf_info['file_path']
        
        if os.path.exists(emf_path):
            with open(emf_path, 'r') as f:
                emf_data = f.read()
            logging.info(f"✅ EMF file loaded: {len(emf_data)} bytes")
        else:
            logging.error(f"❌ EMF file not found: {emf_path}")
            return None, None
        
        return pack_data, (audio_data, emf_data)
        
    except Exception as e:
        logging.error(f"❌ Failed to load auth pack: {e}")
        return None, None

def generate_composite_passphrase(pack_data, audio_data, emf_data):
    """Generate composite passphrase from all authentication factors"""
    
    logging.info("🔐 Generating composite passphrase from stored factors...")
    
    # Get stored NFC hash from pack
    nfc_hash = pack_data['pack_metadata']['nfc_binding_hash']
    logging.info(f"🏷️ Using stored NFC hash: {nfc_hash[:16]}...")
    
    # Hash audio data
    audio_hash = hashlib.sha256(audio_data).hexdigest()
    logging.info(f"🎵 Audio hash: {audio_hash[:16]}...")
    
    # Hash EMF data
    emf_hash = hashlib.sha256(emf_data.encode()).hexdigest()
    logging.info(f"📡 EMF hash: {emf_hash[:16]}...")
    
    # Create composite seed
    composite_seed = f"{nfc_hash}{audio_hash}{emf_hash}"
    
    # Generate strong passphrase using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'mobileshield_ssh_2024',
        iterations=100000,
    )
    
    passphrase_bytes = kdf.derive(composite_seed.encode())
    passphrase = base64.b64encode(passphrase_bytes).decode()[:24]  # 24 char passphrase
    
    logging.info("✅ Composite passphrase generated successfully")
    return passphrase

def generate_ssh_keys(passphrase):
    """Generate SSH key pair with passphrase protection"""
    
    logging.info("🔑 Generating SSH key pair with passphrase protection...")
    
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    public_key = private_key.public_key()
    
    # Serialize private key with passphrase
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )
    
    # Serialize public key
    public_ssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    
    logging.info("✅ SSH key pair generated with passphrase protection")
    return private_pem, public_ssh, passphrase

def save_ssh_keys(private_pem, public_ssh):
    """Save SSH keys to ~/.ssh/ directory"""
    
    logging.info("💾 Saving SSH keys securely...")
    
    # Create timestamp for unique filenames
    timestamp = int(datetime.now().timestamp())
    
    # Define key paths
    ssh_dir = os.path.expanduser('~/.ssh')
    private_key_path = os.path.join(ssh_dir, f'quick_mobileshield_{timestamp}')
    public_key_path = f'{private_key_path}.pub'
    
    # Ensure .ssh directory exists
    os.makedirs(ssh_dir, exist_ok=True)
    
    # Save private key
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    os.chmod(private_key_path, 0o600)
    
    # Save public key
    with open(public_key_path, 'wb') as f:
        f.write(public_ssh)
    os.chmod(public_key_path, 0o644)
    
    logging.info("✅ SSH keys saved successfully")
    return private_key_path, public_key_path

def update_ssh_config(private_key_path):
    """Update SSH config for GitHub"""
    
    logging.info("⚙️ Setting up SSH configuration...")
    
    ssh_config_path = os.path.expanduser('~/.ssh/config')
    
    # Create SSH config entry
    config_entry = f"""
# MobileShield Secure GitHub Authentication
Host github-nfc-auth
    HostName github.com
    User git
    IdentityFile {private_key_path}
    IdentitiesOnly yes
"""
    
    # Append to SSH config
    with open(ssh_config_path, 'a') as f:
        f.write(config_entry)
    
    logging.info("✅ SSH configuration updated")

def main():
    """Main execution function"""
    
    print("🔐 QUICK SSH KEY GENERATOR")
    print("=" * 40)
    print("Uses existing USB authentication pack")
    print()
    
    # Step 1: Find USB drive
    logging.info("📱 Step 1: Finding USB drive...")
    usb_path = find_usb_drive()
    if not usb_path:
        print("❌ No USB drive with authentication pack found")
        return False
    
    print(f"✅ Found USB: {usb_path}")
    
    # Step 2: Load authentication pack
    logging.info("🔐 Step 2: Loading authentication pack...")
    pack_data, file_data = load_auth_pack(usb_path)
    if not pack_data:
        print("❌ Failed to load authentication pack")
        return False
    
    audio_data, emf_data = file_data
    print("✅ Authentication pack loaded")
    print(f"   NFC Hash: {pack_data['pack_metadata']['nfc_binding_hash'][:16]}...")
    print(f"   Audio: {len(audio_data)} bytes")
    print(f"   EMF: {len(emf_data)} bytes")
    
    # Step 3: Generate passphrase
    logging.info("🔐 Step 3: Generating secure passphrase...")
    passphrase = generate_composite_passphrase(pack_data, audio_data, emf_data)
    print("✅ Secure passphrase generated from all factors")
    
    # Step 4: Generate SSH keys
    logging.info("🔑 Step 4: Generating SSH keys...")
    private_pem, public_ssh, passphrase = generate_ssh_keys(passphrase)
    print("✅ SSH key pair generated with passphrase protection")
    
    # Step 5: Save SSH keys
    logging.info("💾 Step 5: Saving SSH keys...")
    private_key_path, public_key_path = save_ssh_keys(private_pem, public_ssh)
    print("✅ SSH keys saved securely!")
    print(f"   Private key: {private_key_path}")
    print(f"   Public key: {public_key_path}")
    
    # Step 6: Update SSH config
    update_ssh_config(private_key_path)
    print("✅ SSH config updated (Host: github-nfc-auth)")
    
    # Step 7: Display public key for GitHub
    print()
    print("🔗 ADD TO GITHUB SSH KEYS:")
    print("=" * 40)
    print(public_ssh.decode().strip())
    print()
    print("📋 PASSPHRASE (save securely):")
    print("=" * 40)
    print(f"Passphrase: {passphrase}")
    print()
    print("🧪 TEST CONNECTION:")
    print("=" * 40)
    print("ssh -T github-nfc-auth")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logging.info("🎉 Quick SSH key generation completed successfully")
        else:
            logging.error("❌ Quick SSH key generation failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
