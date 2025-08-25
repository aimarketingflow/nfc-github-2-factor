#!/usr/bin/env python3
"""
NFC Writer Test - Tests NFC writing with pre-generated chaos values
Loads chaos values from vault and attempts to write to NFC tags
"""

import os
import pickle
import time
import getpass
from smartcard.System import readers
from smartcard.util import toHexString, toBytes

class NFCWriterTest:
    """Test NFC writing with chaos values from vault"""
    
    def __init__(self):
        self.reader = None
        self.connection = None
        self.chaos_values = []
        self.storage_file = '.chaos_vault'
        
    def load_vault(self):
        """Load chaos values from vault"""
        if not os.path.exists(self.storage_file):
            print("❌ No chaos vault found")
            print("   Run nesdr_chaos_generator.py first")
            return False
            
        try:
            with open(self.storage_file, 'rb') as f:
                vault_data = pickle.load(f)
            
            self.chaos_values = vault_data.get('values', [])
            count = vault_data.get('count', 0)
            
            if count > 0:
                print(f"✅ Vault loaded: {count} chaos values available")
                return True
            else:
                print("❌ Vault is empty")
                print("   Generate values with nesdr_chaos_generator.py")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load vault: {e}")
            return False
    
    def save_vault(self):
        """Save updated vault after using values"""
        try:
            vault_data = {
                'timestamp': time.time(),
                'count': len(self.chaos_values),
                'values': self.chaos_values
            }
            
            with open(self.storage_file, 'wb') as f:
                pickle.dump(vault_data, f)
                
        except Exception:
            pass
    
    def find_nfc_reader(self):
        """Find ACR122U or compatible NFC reader"""
        print("\n🔍 Searching for NFC readers...")
        
        reader_list = readers()
        
        if not reader_list:
            print("❌ No PC/SC readers found")
            print("   Please connect ACR122U reader")
            return False
        
        for r in reader_list:
            name = str(r)
            print(f"   Found: {name}")
            
            # Check for ACR122U or other NFC readers
            if 'ACR122' in name or 'NFC' in name.upper():
                self.reader = r
                print(f"✅ Using NFC reader: {name}")
                return True
        
        # Try first reader if no specific NFC reader found
        self.reader = reader_list[0]
        print(f"⚠️  Using reader: {self.reader}")
        print("   May not support NFC writing")
        return True
    
    def connect_reader(self):
        """Connect to NFC reader"""
        try:
            self.connection = self.reader.createConnection()
            self.connection.connect()
            print("✅ Connected to reader")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_card_uid(self):
        """Get UID of current card"""
        try:
            # Get UID command
            GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = self.connection.transmit(GET_UID)
            
            if sw1 == 0x90 and sw2 == 0x00:
                uid_hex = toHexString(data)
                print(f"   Card UID: {uid_hex[:2]}:••:••:••")
                return data
            else:
                return None
        except:
            return None
    
    def write_block(self, block_num, data):
        """Write 4 bytes to specific block"""
        try:
            # Mifare Classic write command structure
            # Load authentication key
            LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06, 
                       0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # Default key
            
            # Authenticate
            AUTH = [0xFF, 0x86, 0x00, 0x00, 0x05,
                   0x01,  # Version
                   0x00,  # Always 0x00
                   block_num,  # Block to authenticate
                   0x60,  # Key type A
                   0x00]  # Key number
            
            # Write command
            WRITE = [0xFF, 0xD6, 0x00, block_num, 0x04] + list(data)
            
            # Execute commands
            self.connection.transmit(LOAD_KEY)
            self.connection.transmit(AUTH)
            data_out, sw1, sw2 = self.connection.transmit(WRITE)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def test_write_chaos(self):
        """Test writing chaos value to NFC tag"""
        
        if not self.chaos_values:
            print("❌ No chaos values available")
            return False
        
        print("\n" + "=" * 50)
        print("   NFC CHAOS WRITE TEST")
        print("=" * 50)
        
        # Get chaos value
        chaos_value = self.chaos_values[0]  # Peek at first value
        print("\n✅ Chaos value loaded [HIDDEN]")
        print(f"   Value size: {len(chaos_value)} bytes")
        
        print("\n📟 Place NFC tag on reader...")
        input("   Press Enter when ready...")
        
        # Check for card
        uid = self.get_card_uid()
        if not uid:
            print("❌ No card detected")
            return False
        
        print("✅ Card detected!")
        
        # Test write options
        print("\n🧪 Testing write capabilities...")
        
        # Try writing to user data area (block 4+)
        test_blocks = [4, 5, 6, 8, 9, 10]  # Common writable blocks
        writable_blocks = []
        
        for block in test_blocks:
            print(f"   Testing block {block}...", end='')
            # Try writing test pattern
            test_data = bytes([0xCA, 0xFE, 0xBA, 0xBE])
            if self.write_block(block, test_data):
                print(" ✓ Writable")
                writable_blocks.append(block)
            else:
                print(" ✗ Protected")
        
        if not writable_blocks:
            print("\n❌ No writable blocks found")
            print("   Card may be read-only or locked")
            return False
        
        print(f"\n✅ Found {len(writable_blocks)} writable blocks")
        
        # Write chaos value
        choice = input("\nWrite chaos value to tag? (y/n): ")
        if choice.lower() == 'y':
            # Use chaos value
            chaos_value = self.chaos_values.pop(0)  # Remove from vault
            
            # Write to first available block
            target_block = writable_blocks[0]
            print(f"\n✍️  Writing chaos to block {target_block}...")
            
            if self.write_block(target_block, chaos_value):
                print("✅ Chaos value written successfully!")
                print("   Value: [HIDDEN]")
                print(f"   Written to block: {target_block}")
                
                # Save updated vault
                self.save_vault()
                print(f"\n📦 Vault updated: {len(self.chaos_values)} values remaining")
                
                return True
            else:
                print("❌ Write failed")
                # Put value back
                self.chaos_values.insert(0, chaos_value)
                return False
        
        return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
        
        print("\n🔒 Writer test closed")

def main():
    """Test NFC writing with chaos values"""
    
    writer = NFCWriterTest()
    
    print("=" * 60)
    print("   NFC WRITER TEST")
    print("=" * 60)
    print("\n📝 Tests NFC writing with pre-generated chaos values")
    
    # Load vault
    if not writer.load_vault():
        return
    
    # Find reader
    if not writer.find_nfc_reader():
        return
    
    # Connect
    if not writer.connect_reader():
        return
    
    while True:
        print("\n" + "=" * 40)
        print("OPTIONS:")
        print(f"1. Test write chaos value ({len(writer.chaos_values)} available)")
        print("2. Check card UID")
        print("3. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == '1':
            writer.test_write_chaos()
            
        elif choice == '2':
            print("\n📟 Place card on reader...")
            input("   Press Enter when ready...")
            uid = writer.get_card_uid()
            if uid:
                print("✅ Card detected")
            else:
                print("❌ No card found")
                
        elif choice == '3':
            writer.cleanup()
            break

if __name__ == "__main__":
    main()
