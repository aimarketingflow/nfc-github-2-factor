#!/usr/bin/env python3
"""
Quick Test Workflow - Non-blocking USB+NFC+Audio system test
Tests each component individually to prevent hanging
"""

import os
import json
import time
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quick_test_workflow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class QuickTestWorkflow:
    """Non-blocking test workflow for USB+NFC+Audio system"""
    
    def __init__(self):
        self.usb_paths = ["/Volumes/SILVER", "/Volumes/USB", "/Volumes/Untitled", "/Volumes/BLUESAM"]
        
    def test_usb_detection(self):
        """Test USB drive detection"""
        logging.info("🔍 Testing USB drive detection...")
        
        for usb_path in self.usb_paths:
            if os.path.exists(usb_path):
                logging.info(f"✅ USB found: {usb_path}")
                return usb_path
        
        logging.error("❌ No USB drive detected")
        return None
    
    def test_auth_pack_exists(self, usb_path):
        """Test if authentication pack exists"""
        logging.info("📦 Testing authentication pack...")
        
        pack_path = os.path.join(usb_path, "mobileshield_auth_pack.json")
        auth_folder = os.path.join(usb_path, "mobileshield_auth_data")
        
        if os.path.exists(pack_path):
            logging.info("✅ Authentication pack found")
            
            if os.path.exists(auth_folder):
                logging.info("✅ Authentication data folder found")
                
                # List files in auth folder
                try:
                    files = os.listdir(auth_folder)
                    logging.info(f"📁 Auth folder contains {len(files)} files:")
                    for file in files:
                        file_path = os.path.join(auth_folder, file)
                        size = os.path.getsize(file_path)
                        logging.info(f"   - {file} ({size} bytes)")
                    return True
                except Exception as e:
                    logging.error(f"❌ Error reading auth folder: {e}")
                    return False
            else:
                logging.error("❌ Authentication data folder missing")
                return False
        else:
            logging.error("❌ Authentication pack not found")
            return False
    
    def test_nfc_scanner_import(self):
        """Test NFC scanner import"""
        logging.info("📱 Testing NFC scanner import...")
        
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            logging.info("✅ NFC scanner imported successfully")
            return True
        except Exception as e:
            logging.error(f"❌ NFC scanner import failed: {e}")
            return False
    
    def test_crypto_imports(self):
        """Test cryptography imports"""
        logging.info("🔐 Testing cryptography imports...")
        
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            logging.info("✅ Cryptography imports successful")
            return True
        except Exception as e:
            logging.error(f"❌ Cryptography import failed: {e}")
            return False
    
    def suggest_next_steps(self, usb_found, pack_exists, nfc_ok, crypto_ok):
        """Suggest next steps based on test results"""
        
        print("\n🔧 SUGGESTED NEXT STEPS:")
        print("=" * 25)
        
        if not usb_found:
            print("1. Insert USB drive into computer")
            print("2. Ensure USB is mounted and accessible")
            
        elif not pack_exists:
            print("1. Create USB authentication pack first:")
            print("   python3 enhanced_usb_auth_pack.py")
            print("2. This will capture ambient audio + EMF data to USB")
            
        elif not nfc_ok:
            print("1. Check NFC scanner connection")
            print("2. Verify invisible_nfc_scanner.py exists")
            
        elif not crypto_ok:
            print("1. Install cryptography library:")
            print("   pip3 install cryptography")
            
        else:
            print("✅ All components ready!")
            print("1. Run unified authentication:")
            print("   python3 unified_usb_nfc_github_auth.py")
            print("2. Have NFC tag ready for scanning")
    
    def run_quick_test(self):
        """Run complete quick test workflow"""
        
        start_time = datetime.now()
        logging.info(f"🚀 Starting quick test workflow at {start_time}")
        
        print("🧪 QUICK TEST WORKFLOW")
        print("=" * 22)
        print("Testing USB+NFC+Audio system components")
        print()
        
        # Test 1: USB Detection
        usb_path = self.test_usb_detection()
        usb_found = usb_path is not None
        
        # Test 2: Auth Pack (only if USB found)
        pack_exists = False
        if usb_found:
            pack_exists = self.test_auth_pack_exists(usb_path)
        
        # Test 3: NFC Scanner
        nfc_ok = self.test_nfc_scanner_import()
        
        # Test 4: Cryptography
        crypto_ok = self.test_crypto_imports()
        
        # Summary
        total_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📊 TEST RESULTS (completed in {total_duration:.2f}s):")
        print("=" * 35)
        print(f"   USB Drive:        {'✅ Found' if usb_found else '❌ Missing'}")
        print(f"   Auth Pack:        {'✅ Ready' if pack_exists else '❌ Missing'}")
        print(f"   NFC Scanner:      {'✅ Ready' if nfc_ok else '❌ Error'}")
        print(f"   Cryptography:     {'✅ Ready' if crypto_ok else '❌ Error'}")
        
        # Suggest next steps
        self.suggest_next_steps(usb_found, pack_exists, nfc_ok, crypto_ok)
        
        return {
            'usb_found': usb_found,
            'usb_path': usb_path,
            'pack_exists': pack_exists,
            'nfc_ok': nfc_ok,
            'crypto_ok': crypto_ok,
            'all_ready': usb_found and pack_exists and nfc_ok and crypto_ok
        }

if __name__ == "__main__":
    logging.info("🚀 Starting Quick Test Workflow application")
    
    try:
        tester = QuickTestWorkflow()
        results = tester.run_quick_test()
        
        if results['all_ready']:
            logging.info("🎉 All systems ready for unified authentication")
            print(f"\n🎉 SUCCESS! All components ready for GitHub authentication")
        else:
            logging.info("⚠️ Some components need attention")
            print(f"\n⚠️ Some components need setup - see suggestions above")
            
    except KeyboardInterrupt:
        logging.warning("⚠️ Test interrupted by user (Ctrl+C)")
        print("\n⚠️ Test cancelled by user")
    except Exception as e:
        logging.error(f"💥 Unexpected test error: {e}")
        print(f"\n💥 Unexpected error: {e}")
    finally:
        logging.info("🏁 Test workflow complete")
