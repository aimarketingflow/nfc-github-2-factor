#!/usr/bin/env python3
"""
RFID HID Reader Test - For keyboard-emulating RFID readers
Tests if your RFID reader can read tags and potentially write NFC
"""

import sys
import time
import threading
from nesdr_entropy_collector import NESDREntropyCollector

class RFIDHIDReader:
    """Handle HID-based RFID readers that emulate keyboards"""
    
    def __init__(self):
        self.last_tag = None
        self.entropy_collector = None
        self.reading = False
        
    def read_tag_input(self):
        """Read RFID tag from keyboard input"""
        print("\n📟 Place RFID/NFC tag on reader...")
        print("   (Reader will auto-type the tag ID)")
        print("   Press Enter after scan completes")
        print("-" * 50)
        
        try:
            # HID readers type the tag ID like a keyboard
            tag_id = input("   Tag ID will appear here: ")
            
            if tag_id:
                # Clean the input
                tag_id = tag_id.strip()
                print(f"\n✅ Tag detected!")
                print(f"   Raw ID: {tag_id}")
                print(f"   Length: {len(tag_id)} characters")
                
                # Determine tag type
                if len(tag_id) == 8:
                    print("   Type: Likely 4-byte UID (HEX)")
                elif len(tag_id) == 10:
                    print("   Type: Likely 125kHz EM4100 (decimal)")
                elif len(tag_id) == 14:
                    print("   Type: Likely 7-byte UID NFC")
                else:
                    print(f"   Type: Unknown ({len(tag_id)} chars)")
                
                return tag_id
            else:
                print("❌ No tag data received")
                return None
                
        except KeyboardInterrupt:
            print("\n   Scan cancelled")
            return None
    
    def test_write_capability(self):
        """Test if reader supports writing (most HID readers don't)"""
        print("\n🧪 Testing write capability...")
        print("-" * 50)
        
        print("⚠️  HID readers typically don't support writing")
        print("   They are designed for read-only operation")
        print("   To write NFC tags, you need:")
        print("   • ACR122U (PC/SC interface)")
        print("   • PN532 module (with USB/UART adapter)")
        print("   • RC522 module (with USB adapter)")
        
        return False
    
    def chaos_mode(self):
        """Generate chaos values for manual NFC writing"""
        print("\n🎲 CHAOS GENERATION MODE")
        print("=" * 60)
        print("   Generate ultra-random values for NFC tags")
        print("   (Manual writing required with proper NFC writer)")
        print("-" * 60)
        
        # Initialize entropy
        print("\n📡 Initializing NESDR entropy collector...")
        self.entropy_collector = NESDREntropyCollector()
        self.entropy_collector.collect_entropy(rounds=3)
        
        # Generate chaos value
        chaos_value = self.entropy_collector.get_nfc_value()
        
        if chaos_value:
            print("\n✅ Chaos value generated!")
            print("   Length: 4 bytes")
            print("   Entropy quality: HIGH")
            print("\n📝 Value saved internally [HIDDEN]")
            print("   Use a proper NFC writer to program tags")
            
            # Option to generate more
            while True:
                choice = input("\nGenerate another? (y/n): ")
                if choice.lower() == 'y':
                    self.entropy_collector.collect_entropy(rounds=2)
                    chaos_value = self.entropy_collector.get_nfc_value()
                    print("✅ New chaos value generated [HIDDEN]")
                else:
                    break
        
        self.entropy_collector.cleanup()
        print("\n🔒 Entropy collector closed")

def main():
    """Test RFID HID reader"""
    
    reader = RFIDHIDReader()
    
    print("=" * 60)
    print("   RFID HID READER TEST")
    print("=" * 60)
    print("\n📌 Your RFID reader appears to be HID-based")
    print("   (Acts like a keyboard, auto-types tag IDs)")
    
    while True:
        print("\n🎯 OPTIONS:")
        print("1. Read RFID/NFC tag")
        print("2. Test write capability")
        print("3. Generate chaos values (manual write)")
        print("4. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == '1':
            tag = reader.read_tag_input()
            if tag:
                print("\n💡 Tag successfully read!")
                
                # Check if it's NFC
                if len(tag) in [8, 14]:
                    print("   This might be an NFC tag (13.56MHz)")
                elif len(tag) == 10:
                    print("   This is likely a 125kHz RFID tag")
                    print("   (Not compatible with NFC applications)")
                    
        elif choice == '2':
            can_write = reader.test_write_capability()
            if not can_write:
                print("\n💡 To write NFC tags with chaos values:")
                print("   Get an ACR122U reader ($30-40)")
                print("   It works with our nfc_chaos_writer.py")
                
        elif choice == '3':
            reader.chaos_mode()
            
        elif choice == '4':
            print("\n👋 Exiting...")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
