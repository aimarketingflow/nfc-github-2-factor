#!/usr/bin/env python3
"""
RFID Chaos Verifier - Verify NFC tags using HID RFID reader
Uses keyboard-emulating RFID reader to verify chaos values
"""

import os
import pickle
import time
import hashlib

class RFIDChaosVerifier:
    """Verify chaos values using HID RFID reader input"""
    
    def __init__(self):
        self.vault_values = []
        self.storage_file = '.chaos_vault'
        
    def load_vault(self):
        """Load chaos values from vault"""
        if not os.path.exists(self.storage_file):
            print("❌ No chaos vault found")
            print("   Generate values with: python3 nesdr_chaos_generator.py")
            return False
            
        try:
            with open(self.storage_file, 'rb') as f:
                vault_data = pickle.load(f)
            
            self.vault_values = vault_data.get('values', [])
            
            if self.vault_values:
                print(f"✅ Vault loaded: {len(self.vault_values)} values for verification")
                return True
            else:
                print("❌ Vault is empty")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load vault: {e}")
            return False
    
    def hex_to_bytes(self, hex_string):
        """Convert hex string to bytes"""
        try:
            # Remove any spaces, colons, or other separators
            clean_hex = hex_string.replace(" ", "").replace(":", "").replace("-", "")
            
            # Ensure even length
            if len(clean_hex) % 2 != 0:
                clean_hex = "0" + clean_hex
            
            return bytes.fromhex(clean_hex)
        except ValueError:
            return None
    
    def verify_tag_input(self, tag_input):
        """Verify tag input against vault values"""
        if not tag_input:
            return False
            
        # Try different interpretations of the input
        possible_values = []
        
        # 1. Direct hex conversion
        if len(tag_input) >= 8:  # Minimum for 4-byte hex
            hex_bytes = self.hex_to_bytes(tag_input)
            if hex_bytes:
                # Try 4-byte chunks
                for i in range(len(hex_bytes) - 3):
                    possible_values.append(hex_bytes[i:i+4])
        
        # 2. If it's decimal, convert to 4-byte value
        if tag_input.isdigit():
            try:
                decimal_val = int(tag_input)
                # Convert to 4-byte big-endian
                possible_values.append(decimal_val.to_bytes(4, 'big'))
                # Try little-endian too
                possible_values.append(decimal_val.to_bytes(4, 'little'))
            except:
                pass
        
        # Check against vault values
        for test_value in possible_values:
            for i, vault_value in enumerate(self.vault_values):
                if test_value == vault_value:
                    return True, i
        
        return False, -1
    
    def verify_chaos_tag(self):
        """Verify single chaos tag"""
        print("\n" + "=" * 50)
        print("   RFID CHAOS VERIFICATION")
        print("=" * 50)
        
        print("\n📟 Place NFC tag on RFID reader...")
        print("   The reader will type the tag ID automatically")
        print("   Press Enter after the tag ID appears")
        print("-" * 50)
        
        try:
            # Get tag input from HID reader
            tag_input = input("   Tag ID: ").strip()
            
            if not tag_input:
                print("\n❌ No tag data received")
                return False
            
            print(f"\n✅ Tag data captured")
            print(f"   Length: {len(tag_input)} characters")
            print(f"   Format: {'HEX' if any(c in tag_input.lower() for c in 'abcdef') else 'DECIMAL'}")
            
            # Verify against vault
            print("\n🔍 Verifying against chaos vault...")
            
            verified, vault_index = self.verify_tag_input(tag_input)
            
            print("\n" + "=" * 50)
            if verified:
                print("🎯 CHAOS VERIFICATION: ✅ SUCCESS")
                print(f"   Matches vault value #{vault_index + 1}")
                print("   Tag contains valid chaos authentication")
                print("   Values: [HIDDEN - NEVER DISPLAYED]")
                return True
            else:
                print("⚠️  CHAOS VERIFICATION: ❌ FAILED")
                print("   No matching chaos values found")
                print("   Tag may not be chaos-written or corrupted")
                return False
                
        except KeyboardInterrupt:
            print("\n\n❌ Verification cancelled")
            return False
    
    def continuous_verify(self):
        """Continuously verify multiple tags"""
        print("\n🔄 CONTINUOUS VERIFICATION MODE")
        print("   Scan multiple NFC tags with RFID reader")
        print("   Press Ctrl+C to exit")
        
        verified_count = 0
        failed_count = 0
        
        try:
            while True:
                print(f"\n📊 Stats: ✅ {verified_count} verified, ❌ {failed_count} failed")
                print("-" * 30)
                
                if self.verify_chaos_tag():
                    verified_count += 1
                else:
                    failed_count += 1
                
                print("\n💡 Scan next tag or Ctrl+C to exit...")
                
        except KeyboardInterrupt:
            print(f"\n\n📊 VERIFICATION SESSION COMPLETE")
            print(f"   ✅ Verified tags: {verified_count}")
            print(f"   ❌ Failed verifications: {failed_count}")
            print(f"   📈 Success rate: {verified_count/(verified_count+failed_count)*100:.1f}%" if (verified_count+failed_count) > 0 else "   📈 No tags tested")

def main():
    """RFID-based chaos verification"""
    
    verifier = RFIDChaosVerifier()
    
    print("=" * 60)
    print("   RFID CHAOS VERIFIER")
    print("=" * 60)
    print("\n🔍 Verifies NFC tags using HID RFID reader")
    print("🎯 Compares against chaos vault without revealing values")
    print("⌨️  Reader types tag IDs automatically")
    
    # Load vault
    if not verifier.load_vault():
        return
    
    while True:
        print("\n" + "=" * 40)
        print("VERIFICATION OPTIONS:")
        print("1. Verify single tag")
        print("2. Continuous verification mode")
        print("3. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == '1':
            verifier.verify_chaos_tag()
            
        elif choice == '2':
            verifier.continuous_verify()
            
        elif choice == '3':
            print("\n🔒 Verifier closed")
            break

if __name__ == "__main__":
    main()
