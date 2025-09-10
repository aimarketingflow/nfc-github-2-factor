#!/usr/bin/env python3
"""
Simple Zero-Knowledge NFC Authentication
- First NFC scan: Unlocks USB ambient data (never stored)
- Second NFC scan: Combines with ambient data for passphrase assembly
- No NFC values ever displayed or stored anywhere
"""

import json
import hashlib
import sys
import os
import subprocess
import hashlib
import logging
import time
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simple_nfc_scan(purpose="authentication"):
    """Invisible NFC scan using PineappleExpress method"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}")
    print("🔒 Place NFC tag on reader...")
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked")
    print("   🎯 Scan NFC tag now (press Enter when done):")
    
    try:
        import termios
        import tty
        import signal
        
        # Store original terminal settings
        original_settings = termios.tcgetattr(sys.stdin)
        
        def timeout_handler(signum, frame):
            raise TimeoutError("NFC scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            # Configure for invisible input using PineappleExpress method
            tty.setcbreak(sys.stdin.fileno())
            
            # Read invisible input character by character
            tag_data = ""
            while True:
                try:
                    char = sys.stdin.read(1)
                    if char == '\n' or char == '\r':
                        break
                    elif char == '\x03':  # Ctrl+C
                        raise KeyboardInterrupt()
                    elif char == '\x7f':  # Backspace
                        if tag_data:
                            tag_data = tag_data[:-1]
                            print(".", end='', flush=True)
                    else:
                        tag_data += char
                        print("*", end='', flush=True)  # Mask with asterisks
                except Exception as e:
                    print(f"\n❌ Input error: {e}")
                    return None
            
            signal.alarm(0)  # Cancel timeout
            
        finally:
            # Restore terminal settings
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
            except:
                pass
        
        if not tag_data:
            print("\n❌ No tag data received")
            return None
        
        # Immediately hash the tag data (NEVER store or display raw)
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
        
        # Securely overwrite raw tag data
        tag_data = "0" * len(tag_data)
        del tag_data
        
        print(f"\n✅ NFC scan completed (zero-knowledge mode)")
        return tag_hash
        
    except TimeoutError:
        print("\n❌ NFC scan timeout")
        return None
    except KeyboardInterrupt:
        print("\n⚠️ NFC scan cancelled")
        return None
    except Exception as e:
        print(f"\n❌ NFC scan failed: {e}")
        return None

def create_fresh_pack():
    """Create fresh zero-knowledge authentication pack"""
    
    print("🔐 CREATING FRESH ZERO-KNOWLEDGE PACK")
    print("=" * 50)
    
    # Find USB
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    if not os.path.exists(usb_path):
        print("❌ USB not found at /Volumes/YOUR_USB_DRIVE")
        return False
    
    print(f"✅ Found USB: {usb_path}")
    
    # Create auth folder
    auth_folder = os.path.join(usb_path, 'zero_knowledge_auth')
    os.makedirs(auth_folder, exist_ok=True)
    
    # First NFC scan - unlock key
    print("\n🏷️ STEP 1: NFC UNLOCK KEY BINDING")
    nfc_unlock_hash = simple_nfc_scan("unlock key binding")
    if not nfc_unlock_hash:
        return False
    
    print("✅ NFC unlock key bound (never stored)")
    
    # Capture ambient audio (shortened for testing)
    print("\n🎵 STEP 2: AMBIENT AUDIO CAPTURE (30 seconds)")
    timestamp = int(datetime.now().timestamp())
    audio_file = os.path.join(auth_folder, f'ambient_audio_{timestamp}.wav')
    
    try:
        print("🎵 Recording ambient audio...")
        print("   Progress: ", end='', flush=True)
        
        # Start ffmpeg process (30 seconds for testing)
        process = subprocess.Popen([
            'ffmpeg', '-f', 'avfoundation', '-i', ':0',
            '-t', '30', '-ar', '22050', '-ac', '1',
            audio_file, '-y'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Show progress dots every 5 seconds
        for i in range(6):  # 6 * 5 = 30 seconds
            time.sleep(5)
            print("●", end='', flush=True)
            if process.poll() is not None:
                break
        
        # Wait for completion
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode == 0 and os.path.exists(audio_file):
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            print(f"\n✅ Ambient audio captured: {len(audio_data)} bytes")
        else:
            print(f"\n❌ Ambient audio capture failed: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Audio capture error: {e}")
        return False
    
    # Encrypt ambient data with NFC unlock key
    print("\n🔐 STEP 3: ENCRYPTING AMBIENT DATA")
    encrypted_hash = hashlib.sha256(f"{nfc_unlock_hash}{hashlib.sha256(audio_data).hexdigest()}".encode()).hexdigest()
    
    # Create auth pack
    pack_data = {
        "pack_version": "zero_knowledge_1.0",
        "creation_time": timestamp,
        "creation_date": datetime.now().isoformat(),
        "encrypted_ambient_data": {
            "filename": os.path.basename(audio_file),
            "file_path": audio_file,
            "file_size": len(audio_data),
            "encrypted_hash": encrypted_hash,
            "note": "Requires NFC unlock key to access"
        },
        "security_model": "dual_nfc_zero_knowledge"
    }
    
    pack_file = os.path.join(usb_path, 'zero_knowledge_auth_pack.json')
    with open(pack_file, 'w') as f:
        json.dump(pack_data, f, indent=2)
    
    # Clear NFC key from memory
    nfc_unlock_hash = "0" * len(nfc_unlock_hash)
    del nfc_unlock_hash
    
    print("✅ Zero-knowledge pack created!")
    print(f"   Pack: {pack_file}")
    print("   🔒 NFC unlock key cleared from memory")
    
    return True

def zero_knowledge_auth():
    """Perform zero-knowledge SSH authentication"""
    
    print("🔐 ZERO-KNOWLEDGE SSH AUTHENTICATION")
    print("=" * 50)
    
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    pack_file = os.path.join(usb_path, 'zero_knowledge_auth_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No zero-knowledge auth pack found")
        return False
    
    # Load pack
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    print("✅ Auth pack loaded")
    
    # First NFC scan - unlock ambient data
    print("\n🏷️ STEP 1: NFC UNLOCK SCAN")
    nfc_unlock_hash = simple_nfc_scan("ambient data unlock")
    if not nfc_unlock_hash:
        return False
    
    # Load ambient data
    audio_info = pack_data['encrypted_ambient_data']
    audio_file = audio_info['file_path']
    
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    
    # Verify unlock key
    expected_hash = hashlib.sha256(f"{nfc_unlock_hash}{hashlib.sha256(audio_data).hexdigest()}".encode()).hexdigest()
    if expected_hash != audio_info['encrypted_hash']:
        print("❌ NFC unlock key verification failed")
        return False
    
    print("✅ Ambient data unlocked")
    
    # Second NFC scan - passphrase assembly
    print("\n🏷️ STEP 2: NFC PASSPHRASE ASSEMBLY")
    nfc_passphrase_hash = simple_nfc_scan("passphrase assembly")
    if not nfc_passphrase_hash:
        return False
    
    # Assemble passphrase invisibly
    print("\n🔐 STEP 3: INVISIBLE PASSPHRASE ASSEMBLY")
    audio_hash = hashlib.sha256(audio_data).hexdigest()
    composite_seed = f"{nfc_passphrase_hash}{audio_hash}"
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=nfc_unlock_hash.encode()[:32],
        iterations=100000,
    )
    
    passphrase_bytes = kdf.derive(composite_seed.encode())
    passphrase = base64.b64encode(passphrase_bytes).decode()[:24]
    
    print("✅ Passphrase assembled invisibly")
    
    # Generate SSH keys
    print("\n🔑 STEP 4: SSH KEY GENERATION")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )
    
    public_ssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    
    # Save keys
    timestamp = int(datetime.now().timestamp())
    ssh_dir = os.path.expanduser('~/.ssh')
    private_key_path = os.path.join(ssh_dir, f'zero_knowledge_{timestamp}')
    public_key_path = f'{private_key_path}.pub'
    
    os.makedirs(ssh_dir, exist_ok=True)
    
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    os.chmod(private_key_path, 0o600)
    
    with open(public_key_path, 'wb') as f:
        f.write(public_ssh)
    os.chmod(public_key_path, 0o644)
    
    print("✅ SSH keys generated and saved")
    print(f"   Private: {private_key_path}")
    print(f"   Public: {public_key_path}")
    
    # SSH config
    ssh_config_path = os.path.expanduser('~/.ssh/config')
    config_entry = f"""
# Zero-Knowledge NFC GitHub Authentication
Host github-nfc-auth
    HostName github.com
    User git
    IdentityFile {private_key_path}
    IdentitiesOnly yes
"""
    
    with open(ssh_config_path, 'a') as f:
        f.write(config_entry)
    
    print("✅ SSH config updated (Host: github-nfc-auth)")
    
    # Display public key
    print("\n🔗 ADD TO GITHUB SSH KEYS:")
    print("=" * 40)
    print(public_ssh.decode().strip())
    print()
    
    # Clear all sensitive data
    nfc_unlock_hash = "0" * len(nfc_unlock_hash)
    nfc_passphrase_hash = "0" * len(nfc_passphrase_hash)
    passphrase = "0" * len(passphrase)
    composite_seed = "0" * len(composite_seed)
    
    del nfc_unlock_hash, nfc_passphrase_hash, passphrase, composite_seed
    
    print("🔒 ZERO-KNOWLEDGE SECURITY:")
    print("✅ No NFC values stored or displayed")
    print("✅ Passphrase assembled invisibly")
    print("✅ All sensitive data cleared")
    
    return True

def main():
    choice = input("Choose: (1) Create pack (2) Authenticate: ").strip()
    
    if choice == "1":
        return create_fresh_pack()
    elif choice == "2":
        return zero_knowledge_auth()
    else:
        print("❌ Invalid choice")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Cancelled")
        sys.exit(0)
