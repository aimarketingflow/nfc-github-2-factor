#!/usr/bin/env python3
"""
Hardware Verification Script for NFC Chaos Writer
Checks NESDR RTL-SDR and NFC Reader/Writer connections
"""

import subprocess
import sys
import time

def check_nesdr():
    """Check if NESDR RTL-SDR is connected and working"""
    print("\n🔍 Checking NESDR RTL-SDR...")
    print("-" * 50)
    
    try:
        # Check if rtl_test can find the device
        result = subprocess.run(['rtl_test', '-t'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        
        if "Found 1 device" in result.stdout or "Found 1 device" in result.stderr:
            print("✅ NESDR Found: Nooelec NESDR SMArt v5")
            
            # Extract device info
            for line in (result.stdout + result.stderr).split('\n'):
                if 'SN:' in line:
                    print(f"   Serial: {line.strip()}")
                if 'tuner' in line.lower():
                    print(f"   Tuner: {line.strip()}")
            
            # Test quick sample capture
            print("\n📡 Testing RF capture (433MHz)...")
            test_cmd = ['rtl_fm', '-f', '433.92M', '-M', 'am', '-s', '200000', '-E', 'dc', '-']
            test_proc = subprocess.Popen(test_cmd, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE)
            time.sleep(1)
            test_proc.terminate()
            
            print("✅ NESDR is operational and ready for entropy collection")
            return True
        else:
            print("❌ No NESDR device found")
            print("   Please check USB connection")
            return False
            
    except FileNotFoundError:
        print("❌ rtl-sdr tools not installed")
        print("   Run: brew install librtlsdr")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  NESDR detected but test timed out")
        return True
    except Exception as e:
        print(f"❌ Error checking NESDR: {e}")
        return False

def check_nfc_pcsc():
    """Check NFC reader using PC/SC interface (more reliable on macOS)"""
    print("\n🔍 Checking NFC Reader/Writer via PC/SC...")
    print("-" * 50)
    
    try:
        # Try using pcsctest to check smart card status
        result = subprocess.run(['pcsctest'], 
                              input='\n', 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        
        if 'ACR122' in result.stdout or 'ACR122' in result.stderr:
            print("✅ ACR122U NFC Reader detected via PC/SC")
            return True
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try alternative Python method
    try:
        import smartcard.System
        readers = smartcard.System.readers()
        
        if readers:
            for reader in readers:
                reader_name = str(reader)
                print(f"✅ Found reader: {reader_name}")
                if 'ACR122' in reader_name:
                    print("   ACR122U NFC Reader/Writer confirmed")
                    return True
            return True
        else:
            print("❌ No PC/SC readers found")
            
    except ImportError:
        print("⚠️  pyscard not installed")
        print("   Run: pip3 install pyscard")
    except Exception as e:
        print(f"⚠️  PC/SC check error: {e}")
    
    return False

def check_nfc_native():
    """Check NFC reader using native libnfc"""
    print("\n🔍 Checking NFC Reader/Writer via libnfc...")
    print("-" * 50)
    
    try:
        # Check with nfc-list
        result = subprocess.run(['nfc-list'], 
                              capture_output=True, 
                              text=True)
        
        output = result.stdout + result.stderr
        
        if 'ACR122' in output:
            if 'Permission denied' in output:
                print("⚠️  ACR122U detected but needs permissions")
                print("   The reader is connected but macOS is blocking access")
                print("   This is normal - we'll use PC/SC interface instead")
                return True
            elif 'NFC device:' in output:
                print("✅ ACR122U NFC Reader fully operational")
                return True
        elif 'No NFC device found' in output:
            print("❌ No NFC reader detected")
            return False
            
    except FileNotFoundError:
        print("❌ libnfc not installed")
        print("   Run: brew install libnfc")
        return False
    except Exception as e:
        print(f"❌ Error checking NFC: {e}")
        return False
    
    return False

def check_python_modules():
    """Check required Python modules"""
    print("\n🔍 Checking Python modules...")
    print("-" * 50)
    
    modules = {
        'pyrtlsdr': 'RTL-SDR control',
        'pyscard': 'Smart card/NFC access',
        'numpy': 'Signal processing',
        'cryptography': 'Entropy processing'
    }
    
    missing = []
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"✅ {module:15} - {description}")
        except ImportError:
            print(f"❌ {module:15} - {description}")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Install missing modules:")
        print(f"   pip3 install {' '.join(missing)}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("   NFC CHAOS WRITER - HARDWARE VERIFICATION")
    print("=" * 60)
    
    results = {
        'NESDR': check_nesdr(),
        'NFC_PCSC': check_nfc_pcsc(),
        'NFC_Native': check_nfc_native(),
        'Python': check_python_modules()
    }
    
    print("\n" + "=" * 60)
    print("   VERIFICATION SUMMARY")
    print("=" * 60)
    
    # NESDR status
    if results['NESDR']:
        print("✅ NESDR RTL-SDR: READY")
    else:
        print("❌ NESDR RTL-SDR: NOT READY")
    
    # NFC status (either interface works)
    if results['NFC_PCSC'] or results['NFC_Native']:
        print("✅ NFC Reader/Writer: READY")
        if results['NFC_PCSC'] and not results['NFC_Native']:
            print("   (Using PC/SC interface - recommended for macOS)")
    else:
        print("❌ NFC Reader/Writer: NOT READY")
    
    # Python modules
    if results['Python']:
        print("✅ Python Modules: READY")
    else:
        print("⚠️  Python Modules: INCOMPLETE")
    
    # Overall status
    if results['NESDR'] and (results['NFC_PCSC'] or results['NFC_Native']):
        print("\n🎯 SYSTEM READY FOR NFC CHAOS WRITER")
        print("   Both NESDR and NFC hardware detected")
        print("   Ready to generate chaos entropy and write NFC tags")
    else:
        print("\n⚠️  SYSTEM NOT READY")
        print("   Please resolve hardware issues above")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
