#!/usr/bin/env python3
"""
Test ACR122U driver installation
"""

from smartcard.System import readers

def test_driver():
    print("🔍 Testing ACR122U Driver Installation")
    print("=" * 50)
    
    try:
        reader_list = readers()
        
        if not reader_list:
            print("❌ No PC/SC readers found")
            print("💡 Install ACR122U driver and restart macOS")
            return False
        
        print(f"✅ Found {len(reader_list)} reader(s):")
        
        acr_found = False
        for i, reader in enumerate(reader_list):
            reader_name = str(reader)
            print(f"   {i+1}. {reader_name}")
            
            if 'ACR122' in reader_name:
                acr_found = True
                print("      🎯 ACR122U detected!")
                
                # Test connection
                try:
                    conn = reader.createConnection()
                    conn.connect()
                    print("      ✅ Connection successful")
                    conn.disconnect()
                except Exception as e:
                    if "No smart card inserted" in str(e):
                        print("      ✅ Driver working (needs card)")
                    else:
                        print(f"      ❌ Connection failed: {e}")
        
        if acr_found:
            print("\n🎯 ACR122U driver is working!")
            print("   Ready for NFC tag operations")
            return True
        else:
            print("\n⚠️  ACR122U not recognized by PC/SC")
            print("   Check driver installation")
            return False
            
    except Exception as e:
        print(f"❌ PC/SC error: {e}")
        return False

if __name__ == "__main__":
    test_driver()
