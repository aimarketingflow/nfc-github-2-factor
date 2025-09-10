#!/usr/bin/env python3
"""
Test NFC Scanner - Simple test to verify barcode scanner NFC input
"""

import subprocess
import sys
import time

def check_scanner():
    """Check if barcode scanner is detected"""
    
    print("🔍 BARCODE SCANNER TEST")
    print("=" * 23)
    
    try:
        result = subprocess.run(
            ['system_profiler', 'SPUSBDataType'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "BARCODE SCANNER" in result.stdout:
            print("✅ Barcode scanner detected")
            
            # Extract scanner details
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if "BARCODE SCANNER" in line:
                    # Print scanner details
                    for j in range(max(0, i-5), min(len(lines), i+10)):
                        if any(x in lines[j] for x in ['Product ID', 'Vendor ID', 'Location ID']):
                            print(f"   {lines[j].strip()}")
            
            return True
        else:
            print("❌ Barcode scanner not detected")
            return False
            
    except Exception as e:
        print(f"❌ Scanner check failed: {e}")
        return False

def test_input():
    """Test basic input from scanner"""
    
    print("\n📱 NFC INPUT TEST")
    print("=" * 17)
    print("🎯 Scan your NFC tag now...")
    print("   (Data will be visible for testing)")
    print("   Press Ctrl+C to cancel")
    
    try:
        start_time = time.time()
        tag_data = input("Waiting for scan: ")
        end_time = time.time()
        
        if tag_data:
            print(f"\n✅ SUCCESS! Received data:")
            print(f"   Length: {len(tag_data)} characters")
            print(f"   Time: {end_time - start_time:.2f} seconds")
            print(f"   First 10 chars: {tag_data[:10]}...")
            print(f"   Last 10 chars: ...{tag_data[-10:]}")
            return True
        else:
            print("❌ No data received")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled")
        return False
    except Exception as e:
        print(f"\n❌ Input test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 MobileShield NFC Scanner Test")
    print("=" * 33)
    
    # Step 1: Check scanner hardware
    scanner_ok = check_scanner()
    
    if not scanner_ok:
        print("\n❌ Scanner test failed - hardware not detected")
        return False
    
    # Step 2: Test input
    input_ok = test_input()
    
    if input_ok:
        print("\n🎉 NFC scanner test PASSED!")
        print("   Scanner is working correctly")
    else:
        print("\n❌ NFC scanner test FAILED!")
        print("   Check NFC tag placement and try again")
    
    return input_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
