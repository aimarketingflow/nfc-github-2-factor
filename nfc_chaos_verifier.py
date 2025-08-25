#!/usr/bin/env python3
"""
NFC Chaos Verifier - Verifies written chaos values without displaying them
Reads NFC tags and verifies against vault values with complete invisibility
"""

import os
import pickle
import time
import hashlib
from smartcard.System import readers
from smartcard.util import toHexString, toBytes

class NFCChaosVerifier:
    """Verify chaos values on NFC tags without revealing them"""
    
    def __init__(self):
        self.reader = None
        self.connection = None
        self.vault_values = []
        self.storage_file = '.chaos_vault'
        self.written_tags = []  # Track written tag fingerprints
        
    def load_vault(self):
        """Load chaos values for verification"""
        if not os.path.exists(self.storage_file):
            print("❌ No chaos vault found")
            return False
            
        try:
            with open(self.storage_file, 'rb') as f:
                vault_data = pickle.load(f)
            
            self.vault_values = vault_data.get('values', [])
            
            if self.vault_values:
                print(f"✅ Vault loaded: {len(self.vault_values)} values for verification")
                return True
            else:
                print("❌ No values in vault for verification")
                return False
                
        except Exception:
            print("❌ Failed to load vault")
            return False
    
    def find_reader(self):
        """Find any available NFC reader for verification"""
        reader_list = readers()
        
        if not reader_list:
            print("❌ No PC/SC readers found")
            return False
        
        # Use first available reader
        self.reader = reader_list[0]
        print(f"✅ Using reader: {str(self.reader)[:50]}...")
        return True
    
    def connect_reader(self):
        """Connect to reader"""
        try:
            self.connection = self.reader.createConnection()
            self.connection.connect()
            print("✅ Connected to reader")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)[:60]}...")
            return False
    
    def read_block(self, block_num):
        """Read 4 bytes from specific block"""
        try:
            # Load authentication key
            LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06, 
                       0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            
            # Authenticate
            AUTH = [0xFF, 0x86, 0x00, 0x00, 0x05,
                   0x01, 0x00, block_num, 0x60, 0x00]
            
            # Read command
            READ = [0xFF, 0xB0, 0x00, block_num, 0x04]
            
            # Execute commands
            self.connection.transmit(LOAD_KEY)
            self.connection.transmit(AUTH)
            data, sw1, sw2 = self.connection.transmit(READ)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return bytes(data[:4])  # Return 4-byte value
            else:
                return None
                
        except Exception:
            return None
    
    def get_tag_fingerprint(self):
        """Get unique tag fingerprint without revealing UID"""
        try:
            # Get UID command
            GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = self.connection.transmit(GET_UID)
            
            if sw1 == 0x90 and sw2 == 0x00:
                # Create fingerprint hash (don't reveal actual UID)
                uid_hash = hashlib.sha256(bytes(data)).hexdigest()[:8]
                return uid_hash
            else:
                return None
        except:
            return None
    
    def verify_chaos_tag(self):
        """Verify chaos value on tag without displaying it"""
        print("\n" + "=" * 50)
        print("   NFC CHAOS VERIFICATION")
        print("=" * 50)
        
        print("\n📟 Place NFC tag on reader...")
        input("   Press Enter when ready...")
        
        # Get tag fingerprint
        tag_fingerprint = self.get_tag_fingerprint()
        if not tag_fingerprint:
            print("❌ Cannot read tag")
            return False
        
        print(f"✅ Tag detected")
        print(f"   Fingerprint: {tag_fingerprint}")
        
        # Try reading from common chaos write blocks
        test_blocks = [4, 5, 6, 8, 9, 10]
        found_values = []
        
        print("\n🔍 Scanning for chaos values...")
        
        for block in test_blocks:
            print(f"   Block {block}...", end='')
            value = self.read_block(block)
            if value and value != b'\x00\x00\x00\x00':
                found_values.append((block, value))
                print(" [DATA]")
            else:
                print(" [EMPTY]")
        
        if not found_values:
            print("\n❌ No chaos values found on tag")
            print("   Tag may not be written or incompatible")
            return False
        
        print(f"\n✅ Found {len(found_values)} potential chaos value(s)")
        
        # Verify against vault values
        print("\n🧪 Verifying against vault...")
        
        verified_count = 0
        for block, tag_value in found_values:
            # Check against all vault values
            for i, vault_value in enumerate(self.vault_values):
                if tag_value == vault_value:
                    print(f"   Block {block}: ✅ VERIFIED (vault #{i+1})")
                    verified_count += 1
                    break
            else:
                print(f"   Block {block}: ❌ Unknown value")
        
        # Final result
        print("\n" + "=" * 50)
        if verified_count > 0:
            print("🎯 CHAOS VERIFICATION: SUCCESS")
            print(f"   Verified {verified_count} chaos value(s)")
            print("   Tag contains valid chaos authentication")
            
            # Track this tag
            if tag_fingerprint not in self.written_tags:
                self.written_tags.append(tag_fingerprint)
                print(f"   Tag #{len(self.written_tags)} registered")
            
            return True
        else:
            print("⚠️  CHAOS VERIFICATION: FAILED")
            print("   No matching chaos values found")
            print("   Tag may be corrupted or not chaos-written")
            return False
    
    def continuous_verify(self):
        """Continuously verify tags"""
        print("\n🔄 CONTINUOUS VERIFICATION MODE")
        print("   Scan multiple tags to verify chaos values")
        print("   Press Ctrl+C to exit")
        
        verified_tags = 0
        
        try:
            while True:
                print(f"\n📟 Place tag #{verified_tags + 1} on reader...")
                input("   Press Enter (or Ctrl+C to exit)...")
                
                if self.verify_chaos_tag():
                    verified_tags += 1
                    print(f"\n✅ Total verified tags: {verified_tags}")
                else:
                    print("\n❌ Verification failed")
                
                print("-" * 30)
                
        except KeyboardInterrupt:
            print(f"\n\n📊 VERIFICATION SESSION COMPLETE")
            print(f"   Total tags verified: {verified_tags}")
            print(f"   Unique tags tracked: {len(self.written_tags)}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
        
        print("\n🔒 Verifier closed")

def main():
    """Test NFC chaos value verification"""
    
    verifier = NFCChaosVerifier()
    
    print("=" * 60)
    print("   NFC CHAOS VERIFIER")
    print("=" * 60)
    print("\n🔍 Verifies written chaos values without revealing them")
    print("🎯 Values are checked against vault but never displayed")
    
    # Load vault
    if not verifier.load_vault():
        print("\n💡 Generate chaos values first:")
        print("   python3 nesdr_chaos_generator.py")
        return
    
    # Find reader
    if not verifier.find_reader():
        return
    
    # Connect
    if not verifier.connect_reader():
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
            verifier.cleanup()
            break

if __name__ == "__main__":
    main()
