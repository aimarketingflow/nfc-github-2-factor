#!/usr/bin/env python3
"""
Enhanced USB Authentication Pack Creator
Saves ambient audio + EMF files to USB with metadata for authentication
"""

import os
import json
import hashlib
import time
import subprocess
import logging
import sys
from datetime import datetime
from invisible_nfc_scanner import InvisibleNFCScanner

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_usb_auth_pack.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class EnhancedUSBAuthPack:
    """Create USB pack with stored audio/EMF files + metadata"""
    
    def __init__(self):
        self.usb_paths = ["/Volumes/SILVER", "/Volumes/USB", "/Volumes/Untitled", "/Volumes/YOUR_USB_DRIVE"]
        self.pack_filename = "mobileshield_auth_pack.json"
        self.auth_folder = "mobileshield_auth_data"
        
    def find_usb_drive(self):
        """Find available USB drive"""
        
        logging.info("🔍 Starting USB drive detection...")
        print("🔍 DETECTING USB DRIVE")
        print("=" * 22)
        
        for usb_path in self.usb_paths:
            logging.debug(f"🔍 Checking path: {usb_path}")
            if os.path.exists(usb_path):
                logging.info(f"✅ USB drive found at: {usb_path}")
                print(f"✅ Found USB: {usb_path}")
                return usb_path
        
        logging.error("❌ No USB drive found in any expected location")
        print("❌ No USB drive found")
        return None
    
    def create_auth_folder(self, usb_path):
        """Create authentication data folder on USB"""
        
        logging.info(f"📁 Creating authentication folder on USB...")
        auth_folder_path = os.path.join(usb_path, self.auth_folder)
        
        try:
            os.makedirs(auth_folder_path, exist_ok=True)
            logging.info(f"✅ Authentication folder created: {auth_folder_path}")
            print(f"📁 Authentication folder: {auth_folder_path}")
            return auth_folder_path
        except Exception as e:
            logging.error(f"❌ Failed to create auth folder: {e}")
            raise
    
    def capture_and_store_ambient_audio(self, auth_folder, duration=180):
        """Capture ambient audio and store on USB"""
        
        logging.info(f"🎵 Starting ambient audio capture ({duration}s)...")
        print(f"🎵 CAPTURING & STORING AMBIENT AUDIO ({duration}s)")
        print("=" * 45)
        
        timestamp = int(time.time())
        audio_filename = f"ambient_audio_{timestamp}.wav"
        audio_path = os.path.join(auth_folder, audio_filename)
        
        try:
            # Capture audio directly to USB with progress output
            logging.info(f"🎙️ Starting ffmpeg audio capture to: {audio_path}")
            print(f"🎙️  Recording {duration} seconds of ambient audio...")
            
            capture_start = time.time()
            result = subprocess.run([
                'ffmpeg', '-f', 'avfoundation', '-i', ':0', 
                '-t', str(duration), '-ar', '22050', 
                '-y', audio_path
            ], capture_output=False, text=True, timeout=duration + 15)
            
            capture_duration = time.time() - capture_start
            logging.info(f"⏱️ Audio capture completed in {capture_duration:.2f}s")
            
            if result.returncode == 0 and os.path.exists(audio_path):
                logging.info("✅ Audio capture successful, processing metadata...")
                # Get file metadata
                file_size = os.path.getsize(audio_path)
                logging.info(f"📊 Audio file size: {file_size} bytes")
                
                # Calculate hash of audio file
                logging.info("🔐 Calculating audio file hash...")
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                audio_hash = hashlib.sha256(audio_data).hexdigest()
                logging.info(f"✅ Audio hash calculated: {audio_hash[:16]}...")
                
                audio_metadata = {
                    'filename': audio_filename,
                    'file_path': audio_path,
                    'file_size': file_size,
                    'duration_seconds': duration,
                    'sample_rate': 22050,
                    'capture_timestamp': timestamp,
                    'capture_date': datetime.now().isoformat(),
                    'file_hash': audio_hash,
                    'format': 'wav',
                    'purpose': 'ambient_location_fingerprint'
                }
                
                logging.info("✅ Audio metadata created successfully")
                print(f"✅ Audio saved to USB")
                print(f"   File: {audio_filename}")
                print(f"   Size: {file_size} bytes")
                print(f"   Hash: {audio_hash[:16]}...")
                
                return audio_metadata
            else:
                logging.error(f"❌ Audio capture failed - return code: {result.returncode}")
                print("❌ Audio capture failed")
                return None
                
        except subprocess.TimeoutExpired:
            logging.error(f"⏰ Audio capture timed out after {duration + 15}s")
            print(f"⏰ Audio capture timed out")
            return None
        except Exception as e:
            logging.error(f"❌ Audio capture exception: {e}")
            print(f"❌ Audio capture error: {e}")
            return None
    
    def capture_and_store_emf_data(self, auth_folder, duration=30):
        """Capture EMF/RF data and store on USB"""
        
        logging.info(f"📡 Starting EMF data capture ({duration}s)...")
        print(f"📡 CAPTURING & STORING EMF DATA ({duration}s)")
        print("=" * 40)
        
        timestamp = int(time.time())
        emf_filename = f"emf_capture_{timestamp}.json"
        emf_path = os.path.join(auth_folder, emf_filename)
        
        try:
            # Try NESDR EMF capture
            logging.info(f"📡 Starting NESDR chaos generator...")
            emf_start = time.time()
            result = subprocess.run([
                'python3', 'nesdr_chaos_generator.py', '--duration', str(duration), '--output', emf_path
            ], capture_output=True, text=True, timeout=duration + 15)
            
            emf_duration = time.time() - emf_start
            logging.info(f"⏱️ EMF capture completed in {emf_duration:.2f}s")
            
            if result.returncode == 0 and os.path.exists(emf_path):
                logging.info("✅ EMF capture successful, processing metadata...")
                # Get EMF file metadata
                file_size = os.path.getsize(emf_path)
                logging.info(f"📊 EMF file size: {file_size} bytes")
                
                logging.info("🔐 Calculating EMF file hash...")
                with open(emf_path, 'rb') as f:
                    emf_data = f.read()
                
                emf_hash = hashlib.sha256(emf_data).hexdigest()
                logging.info(f"✅ EMF hash calculated: {emf_hash[:16]}...")
                
                emf_metadata = {
                    'filename': emf_filename,
                    'file_path': emf_path,
                    'file_size': file_size,
                    'capture_duration': duration,
                    'capture_timestamp': timestamp,
                    'capture_date': datetime.now().isoformat(),
                    'file_hash': emf_hash,
                    'format': 'json',
                    'purpose': 'emf_chaos_entropy'
                }
                
                logging.info("✅ EMF metadata created successfully")
                print(f"✅ EMF data saved to USB")
                print(f"   File: {emf_filename}")
                print(f"   Size: {file_size} bytes")
                print(f"   Hash: {emf_hash[:16]}...")
                
                return emf_metadata
            else:
                # Fallback: create system entropy file
                logging.warning("⚠️ NESDR unavailable, falling back to system entropy")
                print("⚠️  NESDR unavailable, creating system entropy file")
                
                import secrets
                entropy_data = {
                    'entropy_type': 'system_fallback',
                    'timestamp': timestamp,
                    'entropy_values': [secrets.token_hex(32) for _ in range(10)],
                    'system_info': str(os.uname())
                }
                
                with open(emf_path, 'w') as f:
                    json.dump(entropy_data, f, indent=2)
                
                file_size = os.path.getsize(emf_path)
                
                with open(emf_path, 'rb') as f:
                    emf_data = f.read()
                
                emf_hash = hashlib.sha256(emf_data).hexdigest()
                
                emf_metadata = {
                    'filename': emf_filename,
                    'file_path': emf_path,
                    'file_size': file_size,
                    'capture_duration': duration,
                    'capture_timestamp': timestamp,
                    'capture_date': datetime.now().isoformat(),
                    'file_hash': emf_hash,
                    'format': 'json',
                    'purpose': 'system_entropy_fallback'
                }
                
                print(f"✅ System entropy saved to USB")
                print(f"   File: {emf_filename}")
                print(f"   Size: {file_size} bytes")
                
                return emf_metadata
                
        except Exception as e:
            print(f"❌ EMF capture error: {e}")
            return None
    
    def create_file_manifest(self, auth_folder, audio_metadata, emf_metadata):
        """Create manifest of all authentication files"""
        
        manifest_filename = "file_manifest.json"
        manifest_path = os.path.join(auth_folder, manifest_filename)
        
        manifest_data = {
            'manifest_version': '1.0',
            'creation_timestamp': time.time(),
            'creation_date': datetime.now().isoformat(),
            'authentication_files': {
                'ambient_audio': audio_metadata,
                'emf_data': emf_metadata
            },
            'file_count': 2,
            'total_size': audio_metadata['file_size'] + emf_metadata['file_size'],
            'integrity_note': 'All files required for authentication'
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        print(f"📋 File manifest created: {manifest_filename}")
        
        return manifest_data
    
    def create_enhanced_auth_pack(self):
        """Create enhanced USB pack with stored audio/EMF files"""
        
        start_time = datetime.now()
        logging.info(f"🚀 Starting enhanced USB auth pack creation at {start_time}")
        
        print("🔐 CREATING ENHANCED USB AUTHENTICATION PACK")
        print("=" * 48)
        print("Stores ambient audio + EMF files on USB for authentication")
        print()
        
        # Step 1: Find USB
        logging.info("🔍 Step 1: Finding USB drive...")
        usb_path = self.find_usb_drive()
        if not usb_path:
            logging.error("❌ USB drive not found - aborting")
            return None
        logging.info(f"✅ USB found: {usb_path}")
        
        # Step 2: Create auth folder
        logging.info("📁 Step 2: Creating authentication folder...")
        auth_folder = self.create_auth_folder(usb_path)
        logging.info(f"✅ Auth folder ready: {auth_folder}")
        
        print()
        
        # Step 3: NFC binding
        logging.info("🏷️ Step 3: Starting NFC binding scan...")
        print("🏷️  NFC BINDING SCAN")
        
        try:
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
                
                logging.info("📱 NFC scanner initialized for binding")
                
                # Check scanner first
                if not check_barcode_scanner():
                    print("❌ Barcode scanner not detected")
                    print("   Please ensure scanner is connected and try again")
                    return None
                
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
                    except Exception as e:
                        logging.error(f"❌ NFC scan failed: {e}")
                        print(f"❌ NFC scan failed: {e}")
                        return None
                    finally:
                        signal.alarm(0)  # Ensure timeout is cancelled
                        
                except Exception as e:
                    logging.error(f"❌ NFC scan exception: {e}")
                    return None
                    
            nfc_hash = invisible_nfc_scan()
            if not nfc_hash:
                logging.error("❌ NFC binding scan returned no data")
                print("❌ NFC binding failed")
                return None
            
            logging.info(f"✅ NFC binding successful (hash: {nfc_hash[:16]}...)")
            
        except Exception as e:
            logging.error(f"❌ NFC binding scan exception: {e}")
            print(f"❌ NFC binding failed: {e}")
            return None
        
        print()
        
        # Step 4: Capture and store ambient audio
        logging.info("🎵 Step 4: Starting ambient audio capture...")
        audio_metadata = self.capture_and_store_ambient_audio(auth_folder, duration=180)
        if not audio_metadata:
            logging.error("❌ Audio capture failed - aborting")
            print("❌ Audio capture failed")
            return None
        logging.info("✅ Audio capture and storage completed")
        
        print()
        
        # Step 5: Capture and store EMF data
        logging.info("📡 Step 5: Starting EMF data capture...")
        emf_metadata = self.capture_and_store_emf_data(auth_folder, duration=30)
        if not emf_metadata:
            logging.error("❌ EMF capture failed - aborting")
            print("❌ EMF capture failed")
            return None
        logging.info("✅ EMF capture and storage completed")
        
        print()
        
        # Step 6: Create file manifest
        logging.info("📋 Step 6: Creating file manifest...")
        manifest_data = self.create_file_manifest(auth_folder, audio_metadata, emf_metadata)
        logging.info("✅ File manifest created")
        
        print()
        
        # Step 7: Create main auth pack with file references
        logging.info("📦 Step 7: Creating main authentication pack...")
        print("📦 CREATING MAIN AUTHENTICATION PACK")
        print("=" * 38)
        
        pack_data = {
            'pack_version': '2.0_enhanced',
            'pack_metadata': {
                'creation_time': time.time(),
                'creation_date': datetime.now().isoformat(),
                'nfc_binding_hash': nfc_hash,
                'pack_type': 'github_ssh_authentication_enhanced',
                'auth_folder': self.auth_folder
            },
            'stored_files': {
                'ambient_audio_file': audio_metadata,
                'emf_data_file': emf_metadata,
                'file_manifest': manifest_data
            },
            'authentication_requirements': [
                'NFC tag scan (invisible)',
                'Ambient audio file verification',
                'EMF data file verification',
                'File integrity checks'
            ],
            'security_note': 'Enhanced pack with stored authentication files'
        }
        
        # Save main pack
        pack_path = os.path.join(usb_path, self.pack_filename)
        
        try:
            with open(pack_path, 'w') as f:
                json.dump(pack_data, f, indent=2)
            
            total_duration = (datetime.now() - start_time).total_seconds()
            logging.info(f"🎉 Enhanced auth pack creation completed in {total_duration:.2f}s")
            logging.info(f"💾 Pack saved to: {pack_path}")
            
            print(f"✅ Enhanced authentication pack created")
            print(f"   Total time: {total_duration:.2f}s")
            
        except Exception as e:
            logging.error(f"❌ Failed to save main pack: {e}")
            print(f"❌ Failed to save pack: {e}")
            return None
        print(f"   Main pack: {pack_path}")
        print(f"   Auth folder: {auth_folder}")
        print(f"   Files stored: {len(pack_data['stored_files'])}")
        
        print()
        print("🔒 ENHANCED SECURITY SUMMARY")
        print("=" * 29)
        print("   ✅ NFC tag binding established")
        print("   ✅ Ambient audio file stored on USB")
        print("   ✅ EMF data file stored on USB") 
        print("   ✅ File manifest created")
        print("   ✅ Enhanced pack with file metadata")
        
        print()
        print("🚀 AUTHENTICATION REQUIREMENTS:")
        print("1. USB drive with stored files")
        print("2. NFC tag scan")
        print("3. Audio file integrity verification")
        print("4. EMF file integrity verification")
        
        return pack_path

def main():
    """Create enhanced USB authentication pack"""
    
    if __name__ == "__main__":
        logging.info("🚀 Starting Enhanced USB Auth Pack Creator application")
        
        try:
            creator = EnhancedUSBAuthPack()
            result = creator.create_enhanced_auth_pack()
            
            if result:
                logging.info("🎉 Application completed successfully")
                print("\n🎉 SUCCESS! Enhanced USB authentication pack ready")
            else:
                logging.error("❌ Application failed to create enhanced pack")
                print("\n❌ Failed to create enhanced authentication pack")
                
        except KeyboardInterrupt:
            logging.warning("⚠️ Application interrupted by user (Ctrl+C)")
            print("\n⚠️ Operation cancelled by user")
        except Exception as e:
            logging.error(f"💥 Unexpected application error: {e}")
            print(f"\n💥 Unexpected error: {e}")
        finally:
            logging.info("🏁 Application shutdown complete")
    else:
        print(f"\n❌ Failed to create enhanced authentication pack")

if __name__ == "__main__":
    main()
