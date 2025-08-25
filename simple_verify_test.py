#!/usr/bin/env python3
"""
Simple verification test - Check vault and test tag reading
"""

import os
import pickle

def check_vault():
    """Check chaos vault status"""
    print("🔍 CHECKING CHAOS VAULT")
    print("-" * 30)
    
    if not os.path.exists('.chaos_vault'):
        print("❌ No .chaos_vault file found")
        return False
    
    try:
        with open('.chaos_vault', 'rb') as f:
            vault = pickle.load(f)
        
        count = vault.get('count', 0)
        values = vault.get('values', [])
        
        print(f"✅ Vault file exists")
        print(f"📦 Contains: {count} values")
        print(f"🔢 Actual values: {len(values)} items")
        
        if count > 0:
            print(f"💾 First value size: {len(values[0])} bytes")
            return True
        else:
            print("❌ Vault is empty")
            return False
            
    except Exception as e:
        print(f"❌ Vault error: {e}")
        return False

def test_tag_reading():
    """Test basic tag reading"""
    print("\n🔍 TESTING TAG READING")
    print("-" * 30)
    
    print("📟 Options for verification:")
    print("1. RFID Reader (125kHz) - Can read 125kHz tags only")
    print("2. ACR122U NFC (13.56MHz) - Can read NFC tags")
    
    print("\n💡 If you wrote to an NFC tag with ACR122U:")
    print("   Your RFID reader likely CAN'T read it")
    print("   Different frequencies: 125kHz vs 13.56MHz")
    
    print("\n🧪 Let's test what your RFID reader can see:")
    print("   Place any tag on RFID reader...")
    
    try:
        tag_input = input("   Tag ID (auto-typed): ").strip()
        
        if tag_input:
            print(f"\n✅ RFID reader working!")
            print(f"   Read: {len(tag_input)} characters")
            print(f"   Type: {'HEX' if any(c in tag_input.lower() for c in 'abcdef') else 'DECIMAL'}")
            
            # Try to parse as chaos value
            if len(tag_input) == 8:  # 4 bytes hex
                print(f"   Format: Likely 4-byte UID (good for chaos)")
            elif len(tag_input) == 10:
                print(f"   Format: Likely 125kHz tag (may not be NFC)")
            
            return True
        else:
            print("❌ No tag data received")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
        return False

def main():
    print("=" * 50)
    print("   SIMPLE VERIFICATION TEST")
    print("=" * 50)
    
    # Check vault
    vault_ok = check_vault()
    
    if not vault_ok:
        print("\n💡 Generate chaos values first:")
        print("   python3 nesdr_chaos_generator.py")
        return
    
    # Test reading
    read_ok = test_tag_reading()
    
    print("\n📊 DIAGNOSIS:")
    print("-" * 20)
    if vault_ok and read_ok:
        print("✅ Vault: OK")
        print("✅ Reader: OK")
        print("🎯 Ready for verification!")
    elif vault_ok:
        print("✅ Vault: OK")
        print("❌ Reader: Issue")
        print("💡 Check if RFID reader can read NFC tags")
    else:
        print("❌ Need to generate chaos values first")

if __name__ == "__main__":
    main()
