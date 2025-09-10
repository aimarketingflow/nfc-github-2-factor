#!/usr/bin/env python3
"""
Secure Unified Authentication - Enhanced with SSH key passphrases and rotation
Multi-factor GitHub SSH authentication with encrypted key storage
"""

import os
import json
import hashlib
import time
import logging
import sys
import subprocess
import getpass
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('secure_unified_auth.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def find_usb_drive():
    """Find connected USB drive with authentication pack"""
    
    logging.info("🔍 Starting USB drive detection...")
    
    usb_paths = ["/Volumes/SILVER", "/Volumes/USB", "/Volumes/Untitled", "/Volumes/BLUESAM"]
    
    for path in usb_paths:
        logging.debug(f"🔍 Checking path: {path}")
        if os.path.exists(path):
            pack_path = os.path.join(path, "mobileshield_auth_pack.json")
            if os.path.exists(pack_path):
                logging.info(f"✅ USB drive found at: {path}")
                return path
    
    logging.error("❌ No USB drive with auth pack found")
    return None

def verify_auth_pack(usb_path):
    """Verify USB authentication pack and file integrity"""
    
    logging.info("🔐 Verifying USB authentication pack...")
    
    pack_path = os.path.join(usb_path, "mobileshield_auth_pack.json")
    
    try:
        with open(pack_path, 'r') as f:
            pack_data = json.load(f)
        
        logging.info("✅ Auth pack loaded successfully")
        
        # Check for enhanced format
        if pack_data.get('pack_version') != '2.0_enhanced':
            logging.error("❌ Auth pack not in enhanced format")
            return None, None
        
        # Verify stored files
        stored_files = pack_data.get('stored_files', {})
        auth_folder = os.path.join(usb_path, pack_data['pack_metadata']['auth_folder'])
        
        # Check ambient audio file
        audio_info = stored_files.get('ambient_audio_file', {})
        audio_path = os.path.join(auth_folder, audio_info.get('filename', ''))
        
        if not os.path.exists(audio_path):
            logging.error("❌ Ambient audio file missing or invalid")
            return None, None
        
        # Verify audio file integrity
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        audio_hash = hashlib.sha256(audio_data).hexdigest()
        expected_hash = audio_info.get('file_hash', '')
        
        if audio_hash != expected_hash:
            logging.error("❌ Ambient audio file integrity check failed")
            return None, None
        
        # Check EMF file
        emf_info = stored_files.get('emf_data_file', {})
        emf_path = os.path.join(auth_folder, emf_info.get('filename', ''))
        
        if not os.path.exists(emf_path):
            logging.error("❌ EMF data file missing")
            return None, None
        
        # Verify EMF file integrity
        with open(emf_path, 'rb') as f:
            emf_data = f.read()
        
        emf_hash = hashlib.sha256(emf_data).hexdigest()
        expected_emf_hash = emf_info.get('file_hash', '')
        
        if emf_hash != expected_emf_hash:
            logging.error("❌ EMF data file integrity check failed")
            return None, None
        
        logging.info("🔐 Verifying file integrity...")
        logging.info("✅ All file integrity checks passed")
        
        return pack_data, (audio_data, emf_data)
        
    except Exception as e:
        logging.error(f"❌ Auth pack verification failed: {e}")
        return None, None

def check_barcode_scanner():
    """Check if barcode scanner is connected and ready"""
    
    logging.info("🔍 Checking barcode scanner connection...")
    
    try:
        result = subprocess.run(
            ['system_profiler', 'SPUSBDataType'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "BARCODE SCANNER" in result.stdout:
            logging.info("✅ Barcode scanner detected")
            return True
        else:
            logging.warning("⚠️ Barcode scanner not detected")
            return False
            
    except Exception as e:
        logging.error(f"❌ Scanner check failed: {e}")
        return False

def invisible_nfc_scan():
    """Perform invisible NFC scan without displaying raw data"""
    
    logging.info("🏷️ Starting invisible NFC scan...")
    
    # Check scanner first
    if not check_barcode_scanner():
        print("❌ Barcode scanner not detected")
        print("   Please ensure scanner is connected and try again")
        return None
    
    print("🏷️  NFC AUTHENTICATION")
    print("🔒 Place NFC tag on reader...")
    print("   📱 Barcode scanner detected and ready")
    print("   ⚡ Invisible mode - tag data will NOT appear on screen")
    print("   🎯 Scan NFC tag now...")
    
    try:
        # Use simple input() for barcode scanner auto-typing
        logging.info("⏳ Waiting for NFC tag scan...")
        
        # Set a reasonable timeout for tag scanning
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("NFC scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            # Disable terminal echo for invisible scanning
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set terminal to raw mode to hide input
                tty.setraw(sys.stdin.fileno())
                
                # Read character by character until newline/carriage return
                tag_data = ""
                while True:
                    char = sys.stdin.read(1)
                    if char in ['\n', '\r']:
                        break
                    tag_data += char
                
                signal.alarm(0)  # Cancel timeout
                
            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            if not tag_data:
                logging.error("❌ No tag data received")
                return None
            
            # Immediately hash the tag data
            tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
            
            # Securely clear raw tag data
            tag_data = "0" * len(tag_data)
            tag_data = None
            
            logging.info("✅ NFC scan completed successfully")
            print("✅ NFC tag scanned successfully (invisible mode)")
            return tag_hash
            
        except TimeoutError:
            logging.error("❌ NFC scan timeout")
            print("❌ NFC scan timeout - please try again")
            return None
        finally:
            signal.alarm(0)  # Ensure timeout is cancelled
        
    except Exception as e:
        logging.error(f"❌ NFC scan failed: {e}")
        print(f"❌ NFC scan failed: {e}")
        return None

def generate_passphrase_from_factors(nfc_hash, audio_data, emf_data, pack_data):
    """Generate strong passphrase from all authentication factors"""
    
    logging.info("🔐 Generating composite passphrase from all factors...")
    
    # Combine all entropy sources
    composite_seed = f"{nfc_hash}:{hashlib.sha256(audio_data).hexdigest()}:{hashlib.sha256(emf_data).hexdigest()}:{pack_data['pack_metadata']['nfc_binding_hash']}"
    
    # Generate strong passphrase using PBKDF2
    salt = b"mobileshield_secure_passphrase_v2"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # High iteration count for security
        backend=default_backend()
    )
    
    passphrase_bytes = kdf.derive(composite_seed.encode())
    
    # Convert to base64-like format for SSH compatibility
    import base64
    passphrase = base64.b64encode(passphrase_bytes).decode('ascii')[:32]
    
    logging.info("✅ Composite passphrase generated successfully")
    return passphrase

def generate_secure_ssh_keys(passphrase):
    """Generate SSH key pair with passphrase protection"""
    
    logging.info("🔑 Generating secure SSH key pair with passphrase...")
    
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    # Serialize private key with passphrase encryption
    encrypted_private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    
    logging.info("✅ SSH key pair generated with passphrase protection")
    return encrypted_private_pem, public_pem

def save_ssh_keys_securely(private_key_data, public_key_data):
    """Save SSH keys with secure permissions and rotation support"""
    
    logging.info("💾 Saving SSH keys securely...")
    
    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, exist_ok=True)
    
    timestamp = int(time.time())
    key_name = f"secure_mobileshield_{timestamp}"
    
    private_key_path = os.path.join(ssh_dir, key_name)
    public_key_path = os.path.join(ssh_dir, f"{key_name}.pub")
    
    # Save private key with restrictive permissions
    with open(private_key_path, 'wb') as f:
        f.write(private_key_data)
    os.chmod(private_key_path, 0o600)
    
    # Save public key
    public_key_with_comment = public_key_data.decode() + f" secure-mobileshield@{os.uname().nodename}"
    with open(public_key_path, 'w') as f:
        f.write(public_key_with_comment)
    os.chmod(public_key_path, 0o644)
    
    logging.info("✅ SSH keys saved successfully")
    return private_key_path, public_key_path, public_key_with_comment

def setup_ssh_config(private_key_path):
    """Setup SSH config for secure GitHub access"""
    
    logging.info("⚙️ Setting up SSH configuration...")
    
    ssh_dir = os.path.expanduser("~/.ssh")
    config_path = os.path.join(ssh_dir, "config")
    
    # Create SSH config entry
    config_entry = f"""
# MobileShield Secure GitHub Authentication
Host github-secure
    HostName github.com
    User git
    IdentityFile {private_key_path}
    IdentitiesOnly yes
    AddKeysToAgent yes
    UseKeychain yes

"""
    
    # Append to SSH config
    with open(config_path, 'a') as f:
        f.write(config_entry)
    
    os.chmod(config_path, 0o600)
    
    logging.info("✅ SSH configuration updated")
    return "github-secure"

def test_github_connection(private_key_path, passphrase):
    """Test GitHub SSH connection with passphrase"""
    
    logging.info("🔗 Testing GitHub SSH connection...")
    
    print("🔗 TESTING SECURE GITHUB CONNECTION")
    print("=" * 35)
    
    try:
        # Test connection using SSH key with passphrase
        env = os.environ.copy()
        env['SSH_ASKPASS_REQUIRE'] = 'never'
        
        # Use ssh-add to load key with passphrase
        ssh_add_process = subprocess.Popen(
            ['ssh-add', private_key_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        stdout, stderr = ssh_add_process.communicate(input=f"{passphrase}\n")
        
        if ssh_add_process.returncode == 0:
            logging.info("✅ SSH key loaded into agent")
            
            # Test GitHub connection
            result = subprocess.run(
                ['ssh', '-T', 'git@github.com', '-i', private_key_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "successfully authenticated" in result.stderr:
                logging.info("✅ GitHub SSH connection successful")
                print("✅ GitHub connection successful!")
                print(f"   {result.stderr.strip()}")
                return True
            else:
                logging.warning("⚠️ GitHub SSH test inconclusive")
                print("⚠️ GitHub SSH test completed")
                print(f"   Output: {result.stderr.strip()}")
                return False
        else:
            logging.error(f"❌ Failed to load SSH key: {stderr}")
            return False
            
    except Exception as e:
        logging.error(f"❌ GitHub connection test failed: {e}")
        return False

def create_key_rotation_script():
    """Create automated key rotation script"""
    
    logging.info("🔄 Creating key rotation script...")
    
    script_content = '''#!/bin/bash
# MobileShield SSH Key Rotation Script
# Run this daily/weekly for maximum security

echo "🔄 MobileShield SSH Key Rotation"
echo "================================"

# Remove old keys from SSH agent
ssh-add -D

# Run secure unified authentication
cd "$(dirname "$0")"
python3 secure_unified_auth.py

echo "🎯 Key rotation complete!"
echo "📋 Remember to update GitHub with new public key"
'''
    
    script_path = "/Users/flowgirl/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2/rotate_keys.sh"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    
    logging.info(f"✅ Key rotation script created: {script_path}")
    return script_path

def main():
    """Main secure authentication workflow"""
    
    start_time = time.time()
    
    print("🔒 SECURE MOBILESHIELD GITHUB AUTHENTICATION")
    print("=" * 44)
    print("Multi-factor authentication with encrypted SSH keys")
    print()
    
    try:
        # Step 1: USB verification
        logging.info("📱 Step 1: USB drive verification...")
        print("🔍 DETECTING USB DRIVE")
        print("=" * 22)
        
        usb_path = find_usb_drive()
        if not usb_path:
            print("❌ USB drive not found")
            return False
        
        print(f"✅ Found USB: {usb_path}")
        
        # Step 2: Auth pack verification
        pack_data, file_data = verify_auth_pack(usb_path)
        if not pack_data or not file_data:
            print("❌ USB authentication pack verification failed")
            return False
        
        audio_data, emf_data = file_data
        
        print("✅ USB authentication pack verified")
        print(f"   Audio file: {pack_data['stored_files']['ambient_audio_file']['filename']} ✓")
        print(f"   EMF file: {pack_data['stored_files']['emf_data_file']['filename']} ✓")
        print()
        
        # Step 3: NFC authentication
        logging.info("🏷️ Step 2: NFC authentication...")
        nfc_hash = invisible_nfc_scan()
        if not nfc_hash:
            print("❌ NFC authentication failed")
            return False
        
        # Verify NFC binding
        expected_nfc = pack_data['pack_metadata']['nfc_binding_hash']
        if nfc_hash != expected_nfc:
            logging.error("❌ NFC tag does not match USB pack binding")
            print("❌ NFC tag authentication failed")
            return False
        
        print("✅ NFC authentication successful")
        print()
        
        # Step 4: Generate secure passphrase
        logging.info("🔐 Step 3: Generating secure passphrase...")
        print("🔐 GENERATING SECURE PASSPHRASE")
        print("=" * 31)
        
        passphrase = generate_passphrase_from_factors(nfc_hash, audio_data, emf_data, pack_data)
        print("✅ Secure passphrase generated from all factors")
        print()
        
        # Step 5: Generate SSH keys
        logging.info("🔑 Step 4: Generating encrypted SSH keys...")
        print("🔑 GENERATING ENCRYPTED SSH KEYS")
        print("=" * 32)
        
        private_key_data, public_key_data = generate_secure_ssh_keys(passphrase)
        print("✅ SSH key pair generated with passphrase protection")
        print()
        
        # Step 6: Save keys securely
        logging.info("💾 Step 5: Saving SSH keys...")
        print("💾 SAVING SECURE SSH KEYS")
        print("=" * 25)
        
        private_key_path, public_key_path, public_key_with_comment = save_ssh_keys_securely(
            private_key_data, public_key_data
        )
        
        print("✅ SSH keys saved securely!")
        print(f"   Private key: {private_key_path}")
        print(f"   Public key: {public_key_path}")
        print()
        
        # Step 7: Setup SSH config
        ssh_host = setup_ssh_config(private_key_path)
        print(f"✅ SSH config updated (Host: {ssh_host})")
        print()
        
        # Step 8: Test GitHub connection
        logging.info("🔗 Step 6: Testing GitHub connection...")
        connection_success = test_github_connection(private_key_path, passphrase)
        print()
        
        # Step 9: Create rotation script
        rotation_script = create_key_rotation_script()
        print(f"🔄 Key rotation script: {rotation_script}")
        print()
        
        # Display results
        elapsed_time = time.time() - start_time
        logging.info(f"🎉 Secure authentication completed in {elapsed_time:.2f}s")
        
        print("📋 PUBLIC KEY FOR GITHUB:")
        print("=" * 50)
        print(public_key_with_comment)
        print("=" * 50)
        print()
        
        print("🔒 SECURITY FEATURES:")
        print("=" * 19)
        print("✅ Multi-factor authentication (USB + NFC + Audio + EMF)")
        print("✅ SSH key passphrase protection")
        print("✅ File integrity verification")
        print("✅ Secure key storage (600 permissions)")
        print("✅ SSH agent integration")
        print("✅ Automated rotation support")
        print()
        
        print("🎯 NEXT STEPS:")
        print("=" * 12)
        print("1. Copy the public key above to GitHub")
        print("2. Remove old SSH keys from GitHub")
        print("3. Test git operations")
        print("4. Run rotation script regularly")
        print()
        
        if connection_success:
            print("🎉 SUCCESS! Secure GitHub authentication ready")
        else:
            print("⚠️  Setup complete - add public key to GitHub")
        
        return True
        
    except KeyboardInterrupt:
        logging.info("🛑 Authentication interrupted by user")
        print("\n🛑 Authentication cancelled")
        return False
    except Exception as e:
        logging.error(f"❌ Authentication failed: {e}")
        print(f"\n❌ Authentication failed: {e}")
        return False
    finally:
        logging.info("🏁 Application shutdown complete")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
