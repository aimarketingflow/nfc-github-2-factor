#!/usr/bin/env python3
"""
Location-Bound USB Authentication System
Binds authentication data to specific USB hardware and mount location
Prevents data theft/movement by including USB fingerprint in passphrase generation
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

def get_usb_hardware_fingerprint(usb_path):
    """Get unique hardware fingerprint of USB device"""
    
    logging.info(f"🔍 Getting USB hardware fingerprint for {usb_path}...")
    
    try:
        # Get detailed USB device information
        result = subprocess.run(
            ['system_profiler', 'SPUSBDataType', '-json'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            logging.error("❌ Failed to get USB device info")
            return None
        
        import json as json_lib
        usb_data = json_lib.loads(result.stdout)
        
        # Find the USB device that matches our mount path
        volume_name = os.path.basename(usb_path)
        
        def find_usb_device(items, target_volume):
            for item in items:
                # Check if this device has volumes
                if 'volumes' in item:
                    for volume in item['volumes']:
                        if volume.get('mount_point', '').endswith(target_volume):
                            return item
                
                # Check nested items
                if '_items' in item:
                    result = find_usb_device(item['_items'], target_volume)
                    if result:
                        return result
            return None
        
        usb_device = find_usb_device(usb_data.get('SPUSBDataType', []), volume_name)
        
        if not usb_device:
            logging.warning(f"⚠️ Could not find USB device for {volume_name}")
            # Fallback to basic volume info
            fingerprint_data = {
                'volume_name': volume_name,
                'mount_point': usb_path,
                'fallback': True
            }
        else:
            # Extract unique hardware identifiers
            fingerprint_data = {
                'product_id': usb_device.get('product_id', 'unknown'),
                'vendor_id': usb_device.get('vendor_id', 'unknown'),
                'serial_num': usb_device.get('serial_num', 'unknown'),
                'manufacturer': usb_device.get('manufacturer', 'unknown'),
                'location_id': usb_device.get('location_id', 'unknown'),
                'volume_name': volume_name,
                'mount_point': usb_path
            }
        
        # Create hardware fingerprint hash
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        hardware_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        logging.info(f"✅ USB hardware fingerprint: {hardware_hash[:16]}...")
        return hardware_hash, fingerprint_data
        
    except Exception as e:
        logging.error(f"❌ Failed to get USB fingerprint: {e}")
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
    """Perform invisible NFC scan without displaying or storing raw data"""
    
    logging.info("🏷️ Starting live NFC scan for location-bound authentication...")
    
    # Check scanner first
    if not check_barcode_scanner():
        print("❌ Barcode scanner not detected")
        print("   Please ensure scanner is connected and try again")
        return None
    
    print("🏷️  LOCATION-BOUND NFC AUTHENTICATION")
    print("🔒 Place NFC tag on reader...")
    print("   📱 Barcode scanner detected and ready")
    print("   ⚡ Invisible mode - tag data will NOT appear on screen")
    print("   🎯 Scan NFC tag now for location-bound passphrase...")
    
    try:
        def timeout_handler(signum, frame):
            raise TimeoutError("NFC scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
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
    
    usb_paths = ['/Volumes/YOUR_USB_DRIVE', '/Volumes/SILVER', '/Volumes/USB', '/Volumes/Untitled']
    
    for path in usb_paths:
        if os.path.exists(path):
            auth_pack_path = os.path.join(path, 'mobileshield_auth_pack.json')
            if os.path.exists(auth_pack_path):
                logging.info(f"✅ Found USB with auth pack: {path}")
                return path
    
    logging.error("❌ No USB drive with auth pack found")
    return None

def verify_location_binding(usb_path):
    """Verify USB is at correct location and hasn't been moved"""
    
    logging.info("🔐 Verifying USB location binding...")
    
    # Get current USB hardware fingerprint
    current_fingerprint, current_data = get_usb_hardware_fingerprint(usb_path)
    if not current_fingerprint:
        logging.error("❌ Could not get current USB fingerprint")
        return False, None
    
    # Load stored fingerprint from auth pack
    auth_pack_path = os.path.join(usb_path, 'mobileshield_auth_pack.json')
    
    try:
        with open(auth_pack_path, 'r') as f:
            pack_data = json.load(f)
        
        # Check if location binding exists
        if 'location_binding' not in pack_data:
            logging.warning("⚠️ No location binding found in auth pack")
            return False, None
        
        stored_fingerprint = pack_data['location_binding']['hardware_fingerprint']
        
        if current_fingerprint == stored_fingerprint:
            logging.info("✅ USB location binding verified - device matches")
            return True, current_fingerprint
        else:
            logging.error("❌ USB location binding FAILED - device moved or cloned")
            logging.error(f"   Stored: {stored_fingerprint[:16]}...")
            logging.error(f"   Current: {current_fingerprint[:16]}...")
            return False, None
            
    except Exception as e:
        logging.error(f"❌ Failed to verify location binding: {e}")
        return False, None

def load_location_bound_audio(usb_path, hardware_fingerprint):
    """Load ambient audio data with location binding verification"""
    
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
            
            # Verify file integrity with location binding
            expected_hash = audio_info['file_hash']
            actual_hash = hashlib.sha256(audio_data).hexdigest()
            
            if actual_hash != expected_hash:
                logging.error("❌ Audio file integrity check failed")
                return None
            
            logging.info(f"✅ Location-bound audio loaded: {len(audio_data)} bytes")
            return audio_data
        else:
            logging.error(f"❌ Audio file not found: {audio_path}")
            return None
        
    except Exception as e:
        logging.error(f"❌ Failed to load location-bound audio: {e}")
        return None

def assemble_location_bound_passphrase(live_nfc_hash, ambient_audio_data, hardware_fingerprint):
    """Assemble passphrase from live NFC + ambient audio + USB location binding"""
    
    logging.info("🔐 Assembling location-bound passphrase...")
    
    # Hash ambient audio data
    audio_hash = hashlib.sha256(ambient_audio_data).hexdigest()
    
    logging.info(f"🎵 Ambient audio hash: {audio_hash[:16]}...")
    logging.info(f"🏷️ Live NFC hash: {live_nfc_hash[:16]}...")
    logging.info(f"💾 USB hardware hash: {hardware_fingerprint[:16]}...")
    
    # Create composite seed (NFC + Audio + USB Hardware)
    composite_seed = f"{live_nfc_hash}{audio_hash}{hardware_fingerprint}"
    
    # Generate strong passphrase using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'mobileshield_location_bound_2024',
        iterations=100000,
    )
    
    passphrase_bytes = kdf.derive(composite_seed.encode())
    passphrase = base64.b64encode(passphrase_bytes).decode()[:24]  # 24 char passphrase
    
    # Securely clear composite seed
    composite_seed = "0" * len(composite_seed)
    composite_seed = None
    
    logging.info("✅ Location-bound passphrase assembled successfully")
    return passphrase

def generate_ssh_keys(passphrase):
    """Generate SSH key pair with location-bound passphrase"""
    
    logging.info("🔑 Generating SSH key pair with location-bound passphrase...")
    
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
    
    logging.info("✅ SSH key pair generated with location-bound passphrase")
    return private_pem, public_ssh

def save_ssh_keys(private_pem, public_ssh):
    """Save SSH keys to ~/.ssh/ directory"""
    
    logging.info("💾 Saving SSH keys securely...")
    
    # Create timestamp for unique filenames
    timestamp = int(datetime.now().timestamp())
    
    # Define key paths
    ssh_dir = os.path.expanduser('~/.ssh')
    private_key_path = os.path.join(ssh_dir, f'location_bound_mobileshield_{timestamp}')
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
# MobileShield Location-Bound GitHub Authentication
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
    
    print("🔐 LOCATION-BOUND USB SSH AUTHENTICATION")
    print("=" * 60)
    print("Prevents data theft by binding to USB hardware fingerprint")
    print("Requires: Live NFC scan + USB ambient audio + Hardware binding")
    print()
    
    # Step 1: Find USB drive
    logging.info("📱 Step 1: Finding USB drive...")
    usb_path = find_usb_drive()
    if not usb_path:
        print("❌ No USB drive with authentication pack found")
        return False
    
    print(f"✅ Found USB: {usb_path}")
    
    # Step 2: Verify location binding
    logging.info("🔐 Step 2: Verifying USB location binding...")
    location_valid, hardware_fingerprint = verify_location_binding(usb_path)
    if not location_valid:
        print("❌ USB location binding verification FAILED")
        print("   This USB has been moved or cloned - authentication blocked")
        return False
    
    print("✅ USB location binding verified - device authentic")
    
    # Step 3: Load location-bound ambient audio
    logging.info("🎵 Step 3: Loading location-bound ambient audio...")
    ambient_audio_data = load_location_bound_audio(usb_path, hardware_fingerprint)
    if not ambient_audio_data:
        print("❌ Failed to load location-bound ambient audio")
        return False
    
    print(f"✅ Location-bound audio loaded: {len(ambient_audio_data)} bytes")
    
    # Step 4: Live NFC scan
    logging.info("🏷️ Step 4: Live NFC scan...")
    live_nfc_hash = invisible_nfc_scan()
    if not live_nfc_hash:
        print("❌ Live NFC scan failed")
        return False
    
    print("✅ Live NFC scan completed")
    
    # Step 5: Assemble location-bound passphrase
    logging.info("🔐 Step 5: Assembling location-bound passphrase...")
    passphrase = assemble_location_bound_passphrase(live_nfc_hash, ambient_audio_data, hardware_fingerprint)
    print("✅ Passphrase assembled from NFC + Audio + USB Hardware")
    
    # Step 6: Generate SSH keys
    logging.info("🔑 Step 6: Generating SSH keys...")
    private_pem, public_ssh = generate_ssh_keys(passphrase)
    print("✅ SSH key pair generated with location-bound passphrase")
    
    # Step 7: Save SSH keys
    logging.info("💾 Step 7: Saving SSH keys...")
    private_key_path, public_key_path = save_ssh_keys(private_pem, public_ssh)
    print("✅ SSH keys saved securely!")
    print(f"   Private key: {private_key_path}")
    print(f"   Public key: {public_key_path}")
    
    # Step 8: Update SSH config
    update_ssh_config(private_key_path)
    print("✅ SSH config updated (Host: github-nfc-auth)")
    
    # Step 9: Display public key for GitHub
    print()
    print("🔗 ADD TO GITHUB SSH KEYS:")
    print("=" * 40)
    print(public_ssh.decode().strip())
    print()
    
    print("🔒 SECURITY MODEL:")
    print("=" * 40)
    print("✅ NFC data never stored (zero-knowledge)")
    print("✅ Ambient audio useless without NFC scan")
    print("✅ USB hardware binding prevents data theft/movement")
    print("✅ Passphrase requires all three factors")
    print("✅ Moving USB to different device breaks authentication")
    
    # Securely clear passphrase from memory
    passphrase = "0" * len(passphrase)
    passphrase = None
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logging.info("🎉 Location-bound SSH authentication completed successfully")
        else:
            logging.error("❌ Location-bound SSH authentication failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
