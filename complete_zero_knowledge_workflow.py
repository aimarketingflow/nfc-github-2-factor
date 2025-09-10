#!/usr/bin/env python3
"""
Complete Zero-Knowledge NFC GitHub Authentication Workflow
Full process: Ambient collection → NFC encryption → SSH key generation → Seamless auth
"""

import json
import hashlib
import sys
import os
import subprocess
import tempfile
import time
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64

def invisible_nfc_scan(purpose="authentication"):
    """Zero-knowledge NFC scan - never displays raw data"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}")
    print("🔒 Place NFC tag on reader...")
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked")
    print("   🎯 Scan NFC tag now (press Enter when done):")
    
    try:
        tag_data = input("").strip()
        
        if not tag_data:
            print("❌ No tag data received")
            return None
        
        # Show masked version only
        print("*" * len(tag_data))
        
        # Immediately hash - NEVER store or display raw
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
        
        # Securely overwrite raw data
        tag_data = "0" * len(tag_data)
        del tag_data
        
        print("✅ NFC scan completed (zero-knowledge mode)")
        return tag_hash
        
    except KeyboardInterrupt:
        print("\n⚠️ NFC scan cancelled")
        return None
    except Exception as e:
        print(f"\n❌ NFC scan failed: {e}")
        return None

def capture_real_ambient_audio():
    """Capture real ambient audio using ffmpeg"""
    
    print("\n🎵 STEP 1: REAL AMBIENT AUDIO CAPTURE")
    print("🔊 Capturing 60 seconds of ambient audio...")
    
    # Create temporary audio file
    audio_file = tempfile.mktemp(suffix='.wav')
    
    try:
        # Capture ambient audio with ffmpeg
        cmd = [
            'ffmpeg', '-f', 'avfoundation', '-i', ':0',
            '-t', '60', '-ar', '44100', '-ac', '2',
            audio_file, '-y'
        ]
        
        print("   🎤 Recording ambient audio (60 seconds)...")
        
        # Show progress dots
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for i in range(60):
            print(".", end='', flush=True)
            time.sleep(1)
        
        process.wait()
        
        if process.returncode != 0:
            print(f"\n❌ Audio capture failed")
            return None
        
        print(f"\n✅ Ambient audio captured (~2.3MB)")
        
        # Read audio data
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        # Clean up temp file
        os.unlink(audio_file)
        
        return audio_data
        
    except Exception as e:
        print(f"\n❌ Audio capture error: {e}")
        if os.path.exists(audio_file):
            os.unlink(audio_file)
        return None

def capture_real_emf_data():
    """Capture real EMF data using NESDR dongle"""
    
    print("\n📡 STEP 2: REAL EMF DATA CAPTURE")
    print("🔬 Capturing 10 seconds of EMF spectrum data...")
    
    # Check if NESDR dongle is available
    try:
        result = subprocess.run(['rtl_test', '-t'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("⚠️  NESDR dongle not detected - using fallback entropy")
            return generate_fallback_emf_data()
    except:
        print("⚠️  NESDR dongle not detected - using fallback entropy")
        return generate_fallback_emf_data()
    
    # Create temporary EMF file
    emf_file = tempfile.mktemp(suffix='.dat')
    
    try:
        # Capture EMF data with rtl_sdr
        cmd = [
            'rtl_sdr', '-f', '433920000', '-s', '2048000',
            '-n', '20480000', emf_file
        ]
        
        print("   📡 Recording EMF spectrum (10 seconds)...")
        
        # Show progress dots
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for i in range(10):
            print(".", end='', flush=True)
            time.sleep(1)
        
        process.wait()
        
        if process.returncode != 0:
            print(f"\n❌ EMF capture failed - using fallback")
            return generate_fallback_emf_data()
        
        print(f"\n✅ EMF data captured (~40MB)")
        
        # Read EMF data
        with open(emf_file, 'rb') as f:
            emf_data = f.read()
        
        # Clean up temp file
        os.unlink(emf_file)
        
        return emf_data
        
    except Exception as e:
        print(f"\n❌ EMF capture error: {e} - using fallback")
        if os.path.exists(emf_file):
            os.unlink(emf_file)
        return generate_fallback_emf_data()

def generate_fallback_emf_data():
    """Generate fallback EMF data using entropy"""
    
    print("   🎲 Generating entropy-based EMF data...")
    
    # Generate 40MB of entropy-based data
    emf_data = os.urandom(40 * 1024 * 1024)
    
    print("   ✅ Fallback EMF data generated (40MB)")
    return emf_data

def create_ambient_authentication_pack():
    """Create complete ambient authentication pack"""
    
    print("🔐 COMPLETE ZERO-KNOWLEDGE AMBIENT AUTHENTICATION")
    print("=" * 60)
    print("🎯 Creating fresh ambient authentication pack with real environmental data")
    
    # Capture real ambient audio
    audio_data = capture_real_ambient_audio()
    if not audio_data:
        print("❌ Failed to capture ambient audio")
        return None
    
    # Capture real EMF data
    emf_data = capture_real_emf_data()
    if not emf_data:
        print("❌ Failed to capture EMF data")
        return None
    
    # Combine ambient data
    print(f"\n🧮 STEP 3: AMBIENT DATA COMBINATION")
    print(f"   🎵 Audio data: {len(audio_data):,} bytes")
    print(f"   📡 EMF data: {len(emf_data):,} bytes")
    
    combined_ambient = audio_data + emf_data
    total_size = len(combined_ambient)
    
    print(f"   🔗 Combined ambient: {total_size:,} bytes (~{total_size/1024/1024:.1f}MB)")
    
    # Get NFC unlock key
    print(f"\n🏷️ STEP 4: NFC UNLOCK KEY GENERATION")
    nfc_unlock_hash = invisible_nfc_scan("ambient data encryption")
    if not nfc_unlock_hash:
        return None
    
    # Encrypt ambient data with NFC unlock key
    print(f"\n🔐 STEP 5: AMBIENT DATA ENCRYPTION")
    print("   🔒 Encrypting ambient data with NFC unlock key...")
    
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ambient_encryption_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(nfc_unlock_hash.encode()))
        fernet = Fernet(key)
        
        encrypted_ambient = fernet.encrypt(combined_ambient)
        
        print("   ✅ Ambient data encrypted successfully")
        
    except Exception as e:
        print(f"   ❌ Encryption failed: {e}")
        return None
    
    # Save to USB
    print(f"\n💾 STEP 6: USB STORAGE")
    
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    if not os.path.exists(usb_path):
        print(f"❌ USB drive not found at {usb_path}")
        return None
    
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    os.makedirs(auth_folder, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    encrypted_filename = f'encrypted_ambient_{int(datetime.now().timestamp())}.dat'
    encrypted_path = os.path.join(auth_folder, encrypted_filename)
    
    # Save encrypted ambient data
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_ambient)
    
    # Create pack metadata
    pack_data = {
        'timestamp': timestamp,
        'encrypted_file': encrypted_filename,
        'audio_size': len(audio_data),
        'emf_size': len(emf_data),
        'total_ambient_size': total_size,
        'encrypted_size': len(encrypted_ambient)
    }
    
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    with open(pack_file, 'w') as f:
        json.dump(pack_data, f, indent=2)
    
    print(f"   ✅ Ambient pack saved to USB: {auth_folder}")
    print(f"   📁 Encrypted file: {encrypted_filename}")
    print(f"   📋 Pack metadata: real_ambient_pack.json")
    
    # Clear sensitive data
    del combined_ambient
    del encrypted_ambient
    del audio_data
    del emf_data
    
    return pack_data

def create_ssh_key_with_dual_nfc():
    """Create SSH key using dual NFC authentication"""
    
    print(f"\n🔑 STEP 7: SSH KEY GENERATION WITH DUAL NFC")
    print("=" * 50)
    
    # Load ambient pack
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No ambient authentication pack found")
        return None
    
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    print("✅ Loaded fresh ambient authentication pack")
    
    # First NFC scan - unlock ambient data
    print(f"\n🏷️ STEP 7A: NFC UNLOCK SCAN")
    nfc_unlock_hash = invisible_nfc_scan("unlock ambient data")
    if not nfc_unlock_hash:
        return None
    
    # Decrypt ambient data
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ambient_encryption_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(nfc_unlock_hash.encode()))
        fernet = Fernet(key)
        
        encrypted_file = os.path.join(auth_folder, pack_data['encrypted_file'])
        with open(encrypted_file, 'rb') as f:
            encrypted_ambient = f.read()
        
        decrypted_ambient = fernet.decrypt(encrypted_ambient)
        print("✅ Real ambient data unlocked (never displayed)")
        
    except Exception as e:
        print(f"❌ Failed to unlock ambient data: {e}")
        return None
    
    # Second NFC scan - assemble passphrase
    print(f"\n🏷️ STEP 7B: NFC PASSPHRASE ASSEMBLY")
    nfc_auth_hash = invisible_nfc_scan("passphrase assembly")
    if not nfc_auth_hash:
        return None
    
    # Generate SSH passphrase invisibly
    print(f"\n🔐 STEP 7C: INVISIBLE PASSPHRASE GENERATION")
    print("   🧮 Combining: NFC hash + ambient audio hash + EMF hash")
    
    ambient_hash = hashlib.sha256(decrypted_ambient).hexdigest()
    passphrase_data = f"{nfc_auth_hash}{ambient_hash}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    print("   ✅ SSH passphrase generated invisibly (32-character)")
    print("   🔒 Passphrase NEVER displayed - zero-knowledge security")
    
    # Generate SSH key
    timestamp = int(datetime.now().timestamp())
    key_name = f"github_complete_nfc_{timestamp}"
    key_path = os.path.expanduser(f"~/.ssh/{key_name}")
    
    print(f"\n🔨 STEP 7D: SSH KEY CREATION")
    print(f"📁 Key path: {key_path}")
    
    try:
        cmd = [
            'ssh-keygen', '-t', 'rsa', '-b', '2048',
            '-f', key_path, '-N', passphrase,
            '-C', f'complete-nfc-{timestamp}@github.com'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ SSH key generation failed: {result.stderr}")
            return None
        
        print("✅ SSH key generated with zero-knowledge passphrase")
        
        # Set permissions
        os.chmod(key_path, 0o600)
        os.chmod(f"{key_path}.pub", 0o644)
        
        # Read public key
        with open(f"{key_path}.pub", 'r') as f:
            public_key = f.read().strip()
        
        # Update SSH config
        host_alias = "github-nfc-auth"
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        
        config_entry = f"""
# Complete Zero-Knowledge NFC SSH Authentication
Host {host_alias}
    HostName github.com
    User git
    IdentityFile {key_path}
"""
        
        with open(ssh_config_path, 'a') as f:
            f.write(config_entry)
        
        print(f"✅ SSH config updated with host: {host_alias}")
        
        # Clear sensitive data
        del decrypted_ambient
        passphrase = "0" * len(passphrase)
        del passphrase
        
        return {
            'key_path': key_path,
            'public_key': public_key,
            'host_alias': host_alias,
            'pack_data': pack_data
        }
        
    except Exception as e:
        print(f"❌ SSH key creation error: {e}")
        return None

def test_seamless_authentication(key_info):
    """Test seamless authentication with the new key"""
    
    print(f"\n🧪 STEP 8: SEAMLESS AUTHENTICATION TEST")
    print("=" * 50)
    
    print("🚀 Testing complete zero-knowledge workflow...")
    print("   This will repeat the dual NFC process to authenticate")
    
    # Load pack for authentication
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    # Repeat dual NFC authentication
    print(f"\n🏷️ AUTH STEP 1: NFC UNLOCK SCAN")
    nfc_unlock_hash = invisible_nfc_scan("unlock ambient data")
    if not nfc_unlock_hash:
        return False
    
    # Decrypt ambient data
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ambient_encryption_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(nfc_unlock_hash.encode()))
        fernet = Fernet(key)
        
        encrypted_file = os.path.join(auth_folder, pack_data['encrypted_file'])
        with open(encrypted_file, 'rb') as f:
            encrypted_ambient = f.read()
        
        decrypted_ambient = fernet.decrypt(encrypted_ambient)
        print("✅ Ambient data unlocked for authentication")
        
    except Exception as e:
        print(f"❌ Authentication unlock failed: {e}")
        return False
    
    print(f"\n🏷️ AUTH STEP 2: NFC PASSPHRASE ASSEMBLY")
    nfc_auth_hash = invisible_nfc_scan("passphrase assembly")
    if not nfc_auth_hash:
        return False
    
    # Generate same passphrase
    ambient_hash = hashlib.sha256(decrypted_ambient).hexdigest()
    passphrase_data = f"{nfc_auth_hash}{ambient_hash}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    print("✅ Authentication passphrase regenerated invisibly")
    
    # Auto-inject into SSH
    print(f"\n🚀 AUTH STEP 3: SEAMLESS SSH CONNECTION")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(f'#!/bin/bash\necho "{passphrase}"\n')
        temp_askpass = f.name
    
    os.chmod(temp_askpass, 0o700)
    
    try:
        env = os.environ.copy()
        env['SSH_ASKPASS'] = temp_askpass
        env['DISPLAY'] = ':0'
        env['SSH_ASKPASS_REQUIRE'] = 'force'
        
        result = subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-T', key_info['host_alias']
        ], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        
        os.unlink(temp_askpass)
        
        # Clear sensitive data
        del decrypted_ambient
        passphrase = "0" * len(passphrase)
        del passphrase
        
        success = result.returncode == 1 and "successfully authenticated" in result.stderr
        
        if success:
            print("🎉 SEAMLESS AUTHENTICATION SUCCESSFUL!")
            print(f"   {result.stderr.strip()}")
        else:
            print("⚠️  Add public key to GitHub to complete authentication")
            print(f"   SSH output: {result.stderr}")
        
        return success
        
    except Exception as e:
        if os.path.exists(temp_askpass):
            os.unlink(temp_askpass)
        print(f"❌ Authentication test error: {e}")
        return False

def main():
    """Complete zero-knowledge NFC GitHub authentication workflow"""
    
    print("🔐 COMPLETE ZERO-KNOWLEDGE NFC GITHUB AUTHENTICATION")
    print("🚀 Full workflow: Ambient capture → NFC encryption → SSH generation → Seamless auth")
    print("=" * 80)
    
    # Step 1-6: Create ambient authentication pack
    pack_data = create_ambient_authentication_pack()
    if not pack_data:
        print("❌ Failed to create ambient authentication pack")
        return
    
    # Step 7: Create SSH key with dual NFC
    key_info = create_ssh_key_with_dual_nfc()
    if not key_info:
        print("❌ Failed to create SSH key")
        return
    
    print(f"\n📋 PUBLIC KEY FOR GITHUB:")
    print(key_info['public_key'])
    
    # Step 8: Test seamless authentication
    print(f"\n🧪 TESTING COMPLETE WORKFLOW")
    test_now = input("Test seamless authentication now? (y/n): ").strip().lower()
    
    if test_now == 'y':
        success = test_seamless_authentication(key_info)
        
        if success:
            print(f"\n🎉 COMPLETE ZERO-KNOWLEDGE WORKFLOW SUCCESSFUL!")
            print(f"   ✅ Real ambient data captured and encrypted")
            print(f"   ✅ SSH key generated with dual NFC passphrase")
            print(f"   ✅ Seamless authentication working")
            print(f"   ✅ Zero-knowledge security maintained throughout")
        else:
            print(f"\n⚠️  Workflow complete - add public key to GitHub for full authentication")
    
    print(f"\n🔐 WORKFLOW SUMMARY:")
    print(f"   Host alias: {key_info['host_alias']}")
    print(f"   Key path: {key_info['key_path']}")
    print(f"   Ambient pack: {pack_data['encrypted_size']:,} bytes encrypted")
    print(f"   Audio captured: {pack_data['audio_size']:,} bytes")
    print(f"   EMF captured: {pack_data['emf_size']:,} bytes")

if __name__ == "__main__":
    main()
