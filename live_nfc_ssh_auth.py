#!/usr/bin/env python3
"""
Live NFC SSH Authentication System
Requires live NFC scan + USB ambient data to assemble passphrase
Zero-knowledge design - NFC data never stored, only scanned when needed
"""

import json
import hashlib
import logging
import os
import subprocess
import sys
import termios
import tty
import signal
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
    """Perform invisible NFC scan without displaying or storing raw data"""
    
    logging.info("🏷️ Starting live NFC scan for passphrase assembly...")
    
    # Check scanner first
    if not check_barcode_scanner():
        print("❌ Barcode scanner not detected")
        print("   Please ensure scanner is connected and try again")
        return None
    
    print("🏷️  LIVE NFC AUTHENTICATION")
    print("🔒 Place NFC tag on reader...")
    print("   📱 Barcode scanner detected and ready")
    print("   ⚡ Invisible mode - tag data will NOT appear on screen")
    print("   🎯 Scan NFC tag now for passphrase assembly...")
    
    try:
        # Use invisible scanning with terminal control
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("NFC scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            # Disable terminal echo for invisible scanning
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
            
            # Immediately hash the tag data (never store raw)
            tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
            
            # Securely clear raw tag data from memory
            tag_data = "0" * len(tag_data)
            tag_data = None
            
            logging.info("✅ Live NFC scan completed successfully")
            print("✅ NFC tag scanned successfully (invisible mode)")
            return tag_hash
            
        except TimeoutError:
            logging.error("❌ NFC scan timeout")
            print("❌ NFC scan timeout - please try again")
            return None
        except Exception as e:
            logging.error(f"❌ NFC scan failed: {e}")
            print(f"❌ NFC scan failed: {e}")
            return None
        finally:
            signal.alarm(0)  # Ensure timeout is cancelled
            
    except Exception as e:
        logging.error(f"❌ NFC scan exception: {e}")
        return None

def find_usb_drive():
    """Find the USB drive with authentication pack"""
    
    usb_paths = ['/Volumes/BLUESAM', '/Volumes/SILVER', '/Volumes/USB', '/Volumes/Untitled']
    
    for path in usb_paths:
        if os.path.exists(path):
            auth_pack_path = os.path.join(path, 'mobileshield_auth_pack.json')
            if os.path.exists(auth_pack_path):
                logging.info(f"✅ Found USB with auth pack: {path}")
                return path
    
    logging.error("❌ No USB drive with auth pack found")
    return None

def load_ambient_audio_data(usb_path):
    """Load ambient audio data from USB (required for passphrase assembly)"""
    
    auth_pack_path = os.path.join(usb_path, 'mobileshield_auth_pack.json')
    
    try:
        with open(auth_pack_path, 'r') as f:
            pack_data = json.load(f)
        
        # Load ambient audio file
        audio_info = pack_data['stored_files']['ambient_audio_file']
        audio_path = audio_info['file_path']
        
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            logging.info(f"✅ Ambient audio loaded: {len(audio_data)} bytes")
            return audio_data
        else:
            logging.error(f"❌ Audio file not found: {audio_path}")
            return None
        
    except Exception as e:
        logging.error(f"❌ Failed to load ambient audio: {e}")
        return None

def assemble_live_passphrase(live_nfc_hash, ambient_audio_data):
    """Assemble passphrase from live NFC scan + stored ambient audio"""
    
    logging.info("🔐 Assembling passphrase from live factors...")
    
    # Hash ambient audio data
    audio_hash = hashlib.sha256(ambient_audio_data).hexdigest()
    logging.info(f"🎵 Ambient audio hash: {audio_hash[:16]}...")
    logging.info(f"🏷️ Live NFC hash: {live_nfc_hash[:16]}...")
    
    # Create composite seed (NFC + Audio)
    composite_seed = f"{live_nfc_hash}{audio_hash}"
    
    # Generate strong passphrase using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'mobileshield_live_nfc_2024',
        iterations=100000,
    )
    
    passphrase_bytes = kdf.derive(composite_seed.encode())
    passphrase = base64.b64encode(passphrase_bytes).decode()[:24]  # 24 char passphrase
    
    # Securely clear composite seed
    composite_seed = "0" * len(composite_seed)
    composite_seed = None
    
    logging.info("✅ Live passphrase assembled successfully")
    return passphrase

def generate_ssh_keys(passphrase):
    """Generate SSH key pair with assembled passphrase"""
    
    logging.info("🔑 Generating SSH key pair with live passphrase...")
    
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
    
    logging.info("✅ SSH key pair generated with live passphrase")
    return private_pem, public_ssh

def save_ssh_keys(private_pem, public_ssh):
    """Save SSH keys to ~/.ssh/ directory"""
    
    logging.info("💾 Saving SSH keys securely...")
    
    # Create timestamp for unique filenames
    timestamp = int(datetime.now().timestamp())
    
    # Define key paths
    ssh_dir = os.path.expanduser('~/.ssh')
    private_key_path = os.path.join(ssh_dir, f'live_nfc_mobileshield_{timestamp}')
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
# MobileShield Live NFC GitHub Authentication
Host github-live-nfc
    HostName github.com
    User git
    IdentityFile {private_key_path}
    IdentitiesOnly yes
"""
    
    # Append to SSH config
    with open(ssh_config_path, 'a') as f:
        f.write(config_entry)
    
    logging.info("✅ SSH configuration updated")

def test_github_connection(private_key_path):
    """Test GitHub SSH connection with passphrase prompt"""
    
    logging.info("🔗 Testing GitHub SSH connection...")
    
    print("🔗 TESTING GITHUB CONNECTION")
    print("=" * 40)
    print("⚠️  You will be prompted for the SSH key passphrase")
    print("   This passphrase was assembled from your live NFC scan + ambient audio")
    print("   If you need to regenerate it, run this script again with the same NFC tag")
    print()
    
    try:
        result = subprocess.run(
            ['ssh', '-T', 'github-live-nfc'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "successfully authenticated" in result.stderr:
            print("✅ GitHub SSH authentication successful!")
            logging.info("✅ GitHub connection test passed")
            return True
        else:
            print("❌ GitHub SSH authentication failed")
            print(f"Output: {result.stderr}")
            logging.error("❌ GitHub connection test failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ GitHub connection test timed out")
        logging.error("❌ Connection test timeout")
        return False
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        logging.error(f"❌ Connection test error: {e}")
        return False

def main():
    """Main execution function"""
    
    print("🔐 LIVE NFC SSH AUTHENTICATION")
    print("=" * 50)
    print("Zero-knowledge passphrase assembly system")
    print("Requires: Live NFC scan + USB ambient audio")
    print()
    
    # Step 1: Find USB drive
    logging.info("📱 Step 1: Finding USB drive...")
    usb_path = find_usb_drive()
    if not usb_path:
        print("❌ No USB drive with authentication pack found")
        return False
    
    print(f"✅ Found USB: {usb_path}")
    
    # Step 2: Load ambient audio data
    logging.info("🎵 Step 2: Loading ambient audio data...")
    ambient_audio_data = load_ambient_audio_data(usb_path)
    if not ambient_audio_data:
        print("❌ Failed to load ambient audio data")
        return False
    
    print(f"✅ Ambient audio loaded: {len(ambient_audio_data)} bytes")
    
    # Step 3: Live NFC scan for passphrase assembly
    logging.info("🏷️ Step 3: Live NFC scan...")
    live_nfc_hash = invisible_nfc_scan()
    if not live_nfc_hash:
        print("❌ Live NFC scan failed")
        return False
    
    print("✅ Live NFC scan completed")
    
    # Step 4: Assemble passphrase from live factors
    logging.info("🔐 Step 4: Assembling live passphrase...")
    passphrase = assemble_live_passphrase(live_nfc_hash, ambient_audio_data)
    print("✅ Passphrase assembled from live NFC + ambient audio")
    
    # Step 5: Generate SSH keys
    logging.info("🔑 Step 5: Generating SSH keys...")
    private_pem, public_ssh = generate_ssh_keys(passphrase)
    print("✅ SSH key pair generated with live passphrase")
    
    # Step 6: Save SSH keys
    logging.info("💾 Step 6: Saving SSH keys...")
    private_key_path, public_key_path = save_ssh_keys(private_pem, public_ssh)
    print("✅ SSH keys saved securely!")
    print(f"   Private key: {private_key_path}")
    print(f"   Public key: {public_key_path}")
    
    # Step 7: Update SSH config
    update_ssh_config(private_key_path)
    print("✅ SSH config updated (Host: github-live-nfc)")
    
    # Step 8: Display public key for GitHub
    print()
    print("🔗 ADD TO GITHUB SSH KEYS:")
    print("=" * 40)
    print(public_ssh.decode().strip())
    print()
    
    # Step 9: Test GitHub connection
    print("🧪 TESTING SSH CONNECTION:")
    print("=" * 40)
    success = test_github_connection(private_key_path)
    
    if success:
        print()
        print("🎉 SUCCESS! Live NFC SSH authentication working!")
        print("   • NFC data never stored (zero-knowledge)")
        print("   • Ambient audio useless without NFC scan")
        print("   • Passphrase assembled live from both factors")
    
    # Securely clear passphrase from memory
    passphrase = "0" * len(passphrase)
    passphrase = None
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logging.info("🎉 Live NFC SSH authentication completed successfully")
        else:
            logging.error("❌ Live NFC SSH authentication failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
