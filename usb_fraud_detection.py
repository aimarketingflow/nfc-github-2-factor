#!/usr/bin/env python3
"""
USB Fraud Detection System
Creates cryptographic hashes and integrity checks to detect fraudulent USB edits
"""

import os
import json
import hashlib
import time
from datetime import datetime
import subprocess

class USBFraudDetector:
    """Detect fraudulent modifications to USB authentication packs"""
    
    def __init__(self):
        self.usb_paths = ["/Volumes/SILVER", "/Volumes/USB", "/Volumes/Untitled", "/Volumes/NO NAME"]
        self.pack_filename = "mobileshield_auth_pack.json"
        self.integrity_filename = "pack_integrity.hash"
        
    def find_usb_drives(self):
        """Find all available USB drives"""
        
        print("🔍 SCANNING FOR USB DRIVES")
        print("=" * 27)
        
        # Check standard mount points
        found_drives = []
        for usb_path in self.usb_paths:
            if os.path.exists(usb_path):
                found_drives.append(usb_path)
                print(f"✅ Found: {usb_path}")
        
        # Also scan /Volumes for any other drives
        try:
            volumes = os.listdir("/Volumes")
            for volume in volumes:
                volume_path = f"/Volumes/{volume}"
                if volume_path not in self.usb_paths and os.path.isdir(volume_path):
                    # Check if it's a removable drive
                    try:
                        stat_result = os.statvfs(volume_path)
                        if stat_result.f_blocks > 0:  # Has storage
                            found_drives.append(volume_path)
                            print(f"✅ Detected: {volume_path}")
                    except:
                        pass
        except:
            pass
        
        if not found_drives:
            print("❌ No USB drives detected")
            print("   Connect USB drive and try again")
        
        return found_drives
    
    def calculate_pack_integrity(self, pack_data):
        """Calculate comprehensive integrity hash for pack"""
        
        # Create deterministic hash of all pack contents
        pack_string = json.dumps(pack_data, sort_keys=True, separators=(',', ':'))
        
        # Multi-layer hashing for fraud detection
        sha256_hash = hashlib.sha256(pack_string.encode()).hexdigest()
        sha512_hash = hashlib.sha512(pack_string.encode()).hexdigest()
        
        # Create composite integrity signature
        composite_data = (
            sha256_hash + 
            sha512_hash + 
            str(len(pack_string)) +
            str(pack_data.get('pack_metadata', {}).get('creation_time', 0))
        ).encode()
        
        integrity_hash = hashlib.blake2b(composite_data, digest_size=32).hexdigest()
        
        integrity_record = {
            'integrity_version': '1.0',
            'creation_time': time.time(),
            'pack_sha256': sha256_hash,
            'pack_sha512': sha512_hash,
            'pack_size': len(pack_string),
            'composite_integrity': integrity_hash,
            'fraud_detection': 'enabled'
        }
        
        return integrity_record
    
    def create_integrity_protection(self, usb_path, pack_data):
        """Create integrity protection for USB pack"""
        
        print("🛡️  CREATING INTEGRITY PROTECTION")
        print("=" * 35)
        
        # Calculate integrity hashes
        integrity_record = self.calculate_pack_integrity(pack_data)
        
        # Save integrity file
        integrity_path = os.path.join(usb_path, self.integrity_filename)
        
        with open(integrity_path, 'w') as f:
            json.dump(integrity_record, f, indent=2)
        
        print(f"✅ Integrity protection created")
        print(f"   SHA256: {integrity_record['pack_sha256'][:16]}...")
        print(f"   SHA512: {integrity_record['pack_sha512'][:16]}...")
        print(f"   Composite: {integrity_record['composite_integrity'][:16]}...")
        print(f"   Protection file: {integrity_path}")
        
        return integrity_record
    
    def verify_pack_integrity(self, usb_path):
        """Verify USB pack hasn't been fraudulently modified"""
        
        print("🔍 VERIFYING PACK INTEGRITY")
        print("=" * 28)
        
        pack_path = os.path.join(usb_path, self.pack_filename)
        integrity_path = os.path.join(usb_path, self.integrity_filename)
        
        # Check if files exist
        if not os.path.exists(pack_path):
            print("❌ Authentication pack not found")
            return False
        
        if not os.path.exists(integrity_path):
            print("❌ Integrity protection not found")
            print("   Pack may be compromised or created without protection")
            return False
        
        try:
            # Load pack and integrity data
            with open(pack_path, 'r') as f:
                pack_data = json.load(f)
            
            with open(integrity_path, 'r') as f:
                stored_integrity = json.load(f)
            
            # Recalculate current integrity
            current_integrity = self.calculate_pack_integrity(pack_data)
            
            # Compare integrity hashes
            integrity_checks = {
                'sha256_match': stored_integrity['pack_sha256'] == current_integrity['pack_sha256'],
                'sha512_match': stored_integrity['pack_sha512'] == current_integrity['pack_sha512'],
                'size_match': stored_integrity['pack_size'] == current_integrity['pack_size'],
                'composite_match': stored_integrity['composite_integrity'] == current_integrity['composite_integrity']
            }
            
            all_checks_passed = all(integrity_checks.values())
            
            print(f"📊 INTEGRITY VERIFICATION RESULTS:")
            print(f"   SHA256 Hash: {'✅ VALID' if integrity_checks['sha256_match'] else '❌ MODIFIED'}")
            print(f"   SHA512 Hash: {'✅ VALID' if integrity_checks['sha512_match'] else '❌ MODIFIED'}")
            print(f"   Pack Size: {'✅ VALID' if integrity_checks['size_match'] else '❌ MODIFIED'}")
            print(f"   Composite: {'✅ VALID' if integrity_checks['composite_match'] else '❌ MODIFIED'}")
            
            if all_checks_passed:
                print(f"\n✅ PACK INTEGRITY VERIFIED - NO FRAUD DETECTED")
                print(f"   Pack is authentic and unmodified")
                return True
            else:
                print(f"\n🚨 FRAUD DETECTED - PACK HAS BEEN MODIFIED")
                print(f"   Pack cannot be trusted for authentication")
                
                # Show what changed
                if not integrity_checks['sha256_match']:
                    print(f"   Original SHA256: {stored_integrity['pack_sha256'][:16]}...")
                    print(f"   Current SHA256:  {current_integrity['pack_sha256'][:16]}...")
                
                return False
                
        except Exception as e:
            print(f"❌ Integrity verification error: {e}")
            return False
    
    def scan_all_usb_drives(self):
        """Scan all USB drives for packs and verify integrity"""
        
        print("🔐 USB FRAUD DETECTION SCAN")
        print("=" * 29)
        print("Scanning all USB drives for authentication packs")
        print()
        
        drives = self.find_usb_drives()
        
        if not drives:
            return []
        
        results = []
        
        for drive in drives:
            print(f"\n📁 SCANNING: {drive}")
            print("=" * (len(drive) + 12))
            
            pack_path = os.path.join(drive, self.pack_filename)
            
            if os.path.exists(pack_path):
                print(f"📦 Found authentication pack")
                
                # Verify integrity
                is_valid = self.verify_pack_integrity(drive)
                
                results.append({
                    'drive_path': drive,
                    'pack_path': pack_path,
                    'integrity_valid': is_valid,
                    'scan_time': time.time()
                })
                
                if is_valid:
                    print(f"🔒 Pack is secure and unmodified")
                else:
                    print(f"⚠️  Pack integrity compromised - DO NOT USE")
            else:
                print(f"📭 No authentication pack found")
        
        print(f"\n📊 SCAN SUMMARY")
        print("=" * 15)
        valid_packs = sum(1 for r in results if r['integrity_valid'])
        total_packs = len(results)
        
        print(f"   USB drives scanned: {len(drives)}")
        print(f"   Auth packs found: {total_packs}")
        print(f"   Valid packs: {valid_packs}")
        print(f"   Compromised packs: {total_packs - valid_packs}")
        
        if total_packs > valid_packs:
            print(f"\n🚨 WARNING: {total_packs - valid_packs} compromised pack(s) detected!")
            print(f"   These packs should not be used for authentication")
        
        return results

def main():
    """Run USB fraud detection scan"""
    
    detector = USBFraudDetector()
    results = detector.scan_all_usb_drives()
    
    if results:
        valid_results = [r for r in results if r['integrity_valid']]
        if valid_results:
            print(f"\n✅ Found {len(valid_results)} valid authentication pack(s)")
            for result in valid_results:
                print(f"   Safe to use: {result['drive_path']}")
        else:
            print(f"\n❌ No valid authentication packs found")
    else:
        print(f"\n📭 No authentication packs detected on any USB drive")

if __name__ == "__main__":
    main()
