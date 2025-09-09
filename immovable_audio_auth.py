#!/usr/bin/env python3
"""
Immovable Audio Authentication System
Creates audio files cryptographically bound to this exact computer
"""

import hashlib
import json
import time
import os
import platform
import subprocess
from datetime import datetime

class ImmovableAudioAuth:
    """System for creating computer-bound audio authentication files"""
    
    def __init__(self):
        self.metadata_prefix = 'com.aimf'
        
    def get_hardware_fingerprint(self):
        """Extract unique hardware characteristics"""
        
        fingerprint_data = {}
        
        try:
            # CPU Information (macOS)
            cpu_info = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
            cpu_cores = subprocess.check_output(['sysctl', '-n', 'hw.ncpu'], text=True).strip()
            
            fingerprint_data['cpu'] = {
                'model': cpu_info,
                'cores': cpu_cores
            }
        except:
            fingerprint_data['cpu'] = {'model': 'unknown'}
        
        try:
            # Memory Configuration
            mem_size = subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True).strip()
            fingerprint_data['memory'] = {'total_bytes': mem_size}
        except:
            fingerprint_data['memory'] = {'total_bytes': '0'}
        
        try:
            # Disk Information
            disk_info = subprocess.check_output(['diskutil', 'info', '/'], text=True)
            for line in disk_info.split('\n'):
                if 'Volume UUID' in line:
                    fingerprint_data['disk_uuid'] = line.split(':')[1].strip()
                elif 'Device / Media Name' in line:
                    fingerprint_data['disk_name'] = line.split(':')[1].strip()
        except:
            fingerprint_data['disk_uuid'] = 'unknown'
        
        # Create hardware hash
        hw_string = str(sorted(fingerprint_data.items()))
        hw_hash = hashlib.sha256(hw_string.encode()).hexdigest()
        
        return hw_hash, fingerprint_data
    
    def get_system_fingerprint(self):
        """Extract system software fingerprint"""
        
        system_data = {}
        
        # Operating System Details
        system_data['os'] = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        
        try:
            # System hostname and user
            hostname = subprocess.check_output(['hostname'], text=True).strip()
            system_data['hostname'] = hostname
            
            whoami = subprocess.check_output(['whoami'], text=True).strip()
            system_data['user'] = whoami
        except:
            system_data['hostname'] = 'unknown'
            system_data['user'] = 'unknown'
        
        try:
            # Installed Applications signature (macOS)
            apps = subprocess.check_output(['ls', '/Applications'], text=True)
            system_data['apps_signature'] = hashlib.sha256(apps.encode()).hexdigest()[:16]
        except:
            system_data['apps_signature'] = 'unknown'
        
        # Create system hash
        sys_string = str(sorted(system_data.items()))
        sys_hash = hashlib.sha256(sys_string.encode()).hexdigest()
        
        return sys_hash, system_data
    
    def get_file_system_binding(self, filepath):
        """Create file system location binding"""
        
        binding_data = {}
        
        try:
            # File system metadata
            file_stat = os.stat(filepath)
            binding_data['inode'] = file_stat.st_ino
            binding_data['device'] = file_stat.st_dev
            binding_data['absolute_path'] = os.path.abspath(filepath)
            binding_data['parent_directory'] = os.path.dirname(os.path.abspath(filepath))
            
            # Directory structure fingerprint
            parent_files = sorted(os.listdir(os.path.dirname(filepath)))
            dir_signature = hashlib.sha256(str(parent_files).encode()).hexdigest()[:16]
            binding_data['directory_signature'] = dir_signature
            
        except Exception as e:
            print(f"   Warning: File system binding limited: {e}")
            binding_data['error'] = str(e)
        
        # Create filesystem hash
        fs_string = str(sorted(binding_data.items()))
        fs_hash = hashlib.sha256(fs_string.encode()).hexdigest()
        
        return fs_hash, binding_data
    
    def get_system_boot_time(self):
        """Get system boot time - changes on reboot"""
        try:
            boot_time = subprocess.check_output(['sysctl', '-n', 'kern.boottime'], text=True)
            return boot_time.strip()
        except:
            return str(time.time())
    
    def generate_copy_detection_signature(self, filepath):
        """Generate signature that changes when file is copied"""
        
        try:
            file_stats = os.stat(filepath)
            
            copy_signature_data = {
                'original_inode': file_stats.st_ino,
                'original_device': file_stats.st_dev,
                'creation_time': file_stats.st_ctime,
                'access_time': file_stats.st_atime,
                'system_boot_time': self.get_system_boot_time()
            }
            
            signature = hashlib.sha256(str(copy_signature_data).encode()).hexdigest()
            return signature
            
        except Exception as e:
            return hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    def create_system_bound_metadata(self, audio_filepath, nfc_hash):
        """Create metadata that cryptographically binds audio to this system"""
        
        print("🔍 Analyzing system fingerprints...")
        
        # Collect all system fingerprints
        hw_hash, hw_data = self.get_hardware_fingerprint()
        sys_hash, sys_data = self.get_system_fingerprint()
        fs_hash, fs_data = self.get_file_system_binding(audio_filepath)
        
        print(f"   Hardware: {hw_hash[:16]}...")
        print(f"   System: {sys_hash[:16]}...")
        print(f"   Filesystem: {fs_hash[:16]}...")
        
        # Create master system signature
        master_signature = hashlib.sha256(
            (hw_hash + sys_hash + fs_hash + nfc_hash).encode()
        ).hexdigest()
        
        # System-bound metadata
        bound_metadata = {
            'format_version': '1.0',
            'creation_timestamp': time.time(),
            'system_binding': {
                'hardware_fingerprint': hw_hash,
                'system_fingerprint': sys_hash,
                'filesystem_binding': fs_hash,
                'nfc_binding': nfc_hash,
                'master_signature': master_signature
            },
            'validation_data': {
                'hardware_details': hw_data,
                'system_details': sys_data,
                'filesystem_details': fs_data
            },
            'security_markers': {
                'immovable_flag': True,
                'copy_detection': self.generate_copy_detection_signature(audio_filepath),
                'creation_host': platform.node(),
                'creation_user': os.getenv('USER', 'unknown')
            }
        }
        
        # Store metadata in file
        self.store_metadata_in_file(audio_filepath, bound_metadata, master_signature)
        
        return master_signature, bound_metadata
    
    def store_metadata_in_file(self, filepath, metadata, signature):
        """Store metadata using multiple methods"""
        
        try:
            # Method 1: Extended attributes (macOS)
            import xattr
            
            metadata_json = json.dumps(metadata)
            xattr.setxattr(filepath, f'{self.metadata_prefix}.system_binding', metadata_json.encode())
            xattr.setxattr(filepath, f'{self.metadata_prefix}.signature', signature.encode())
            xattr.setxattr(filepath, f'{self.metadata_prefix}.bound_flag', b'IMMOVABLE_AUTH_FILE')
            
            print(f"✅ Metadata stored in extended attributes")
            return True
            
        except Exception as e:
            print(f"   Warning: Extended attributes failed: {e}")
            
            # Method 2: Companion metadata file
            try:
                metadata_file = filepath + '.aimf_binding'
                with open(metadata_file, 'w') as f:
                    json.dump({
                        'signature': signature,
                        'metadata': metadata,
                        'bound_flag': 'IMMOVABLE_AUTH_FILE'
                    }, f, indent=2)
                
                print(f"✅ Metadata stored in companion file: {metadata_file}")
                return True
                
            except Exception as e2:
                print(f"❌ Both metadata storage methods failed: {e2}")
                return False
    
    def extract_metadata_from_file(self, filepath):
        """Extract stored metadata from file"""
        
        try:
            # Try extended attributes first
            import xattr
            metadata_json = xattr.getxattr(filepath, f'{self.metadata_prefix}.system_binding')
            return json.loads(metadata_json.decode())
            
        except:
            # Try companion file
            try:
                metadata_file = filepath + '.aimf_binding'
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                        return data['metadata']
                        
            except:
                pass
        
        return None
    
    def validate_system_bound_audio(self, filepath, nfc_hash):
        """Validate that audio file hasn't been moved or copied"""
        
        try:
            # Extract stored metadata
            stored_metadata = self.extract_metadata_from_file(filepath)
            if not stored_metadata:
                return False, "No system binding metadata found"
            
            # Get current system fingerprints
            current_hw_hash, _ = self.get_hardware_fingerprint()
            current_sys_hash, _ = self.get_system_fingerprint()
            current_fs_hash, _ = self.get_file_system_binding(filepath)
            
            # Recreate expected signature
            expected_signature = hashlib.sha256(
                (current_hw_hash + current_sys_hash + current_fs_hash + nfc_hash).encode()
            ).hexdigest()
            
            stored_signature = stored_metadata['system_binding']['master_signature']
            
            # Compare signatures
            if stored_signature != expected_signature:
                return False, "System binding mismatch - file moved or system changed"
            
            # Additional copy detection
            current_copy_sig = self.generate_copy_detection_signature(filepath)
            stored_copy_sig = stored_metadata['security_markers']['copy_detection']
            
            if stored_copy_sig != current_copy_sig:
                return False, "Copy detection triggered - file has been moved"
            
            return True, "System binding validated successfully"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def create_immovable_authentication(self, nfc_hash):
        """Create complete immovable audio authentication"""
        
        print("=" * 60)
        print("   IMMOVABLE AUDIO AUTHENTICATION")
        print("=" * 60)
        
        # 1. Record audio with room acoustics
        print("\n🎵 Recording authentication audio...")
        from song_recorder import SongRecorder
        recorder = SongRecorder()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"immovable_auth_{timestamp}.wav"
        audio_file = recorder.record_song(filename)
        
        if not audio_file:
            print("❌ Audio recording failed")
            return None, None
        
        # 2. Create system binding
        print(f"\n🔒 Binding to computer: {platform.node()}")
        signature, metadata = self.create_system_bound_metadata(audio_file, nfc_hash)
        
        # 3. Test validation
        print(f"\n🔍 Testing immovable binding...")
        is_valid, message = self.validate_system_bound_audio(audio_file, nfc_hash)
        
        if is_valid:
            print("✅ IMMOVABLE AUTHENTICATION CREATED")
            print(f"   File: {audio_file}")
            print(f"   Signature: {signature[:20]}...")
            print(f"   Bound to: {platform.node()}")
            print(f"   User: {os.getenv('USER')}")
            print("\n🚫 SECURITY WARNING:")
            print("   This file will ONLY work on THIS computer")
            print("   Moving, copying, or rebooting may break authentication")
            
            return audio_file, signature
        else:
            print(f"❌ Binding validation failed: {message}")
            return None, None

def main():
    """Interactive immovable audio authentication"""
    
    auth_system = ImmovableAudioAuth()
    
    print("🔐 IMMOVABLE AUDIO AUTHENTICATION SYSTEM")
    print("Creates audio files bound to THIS computer only")
    print()
    
    # Get NFC binding
    print("📟 First, scan your NFC tag for binding...")
    try:
        from invisible_nfc_scanner import InvisibleNFCScanner
        scanner = InvisibleNFCScanner()
        nfc_hash = scanner.invisible_scan_simple()
        print("✅ NFC binding captured")
    except Exception as e:
        print(f"❌ NFC scan failed: {e}")
        print("Using fallback binding method...")
        nfc_hash = hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    # Create immovable authentication
    audio_file, signature = auth_system.create_immovable_authentication(nfc_hash)
    
    if audio_file and signature:
        print(f"\n🎉 SUCCESS! Immovable authentication ready")
        print(f"   Use this file for ultra-secure authentication")
        print(f"   It cannot work on any other computer")
    else:
        print(f"\n❌ Failed to create immovable authentication")

if __name__ == "__main__":
    main()
