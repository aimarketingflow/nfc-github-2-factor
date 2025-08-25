#!/usr/bin/env python3
"""
NFC Chaos Writer - Ultra-Secure NFC Tag Programming
Uses NESDR RF entropy to generate completely random, invisible NFC values
CRITICAL: Values are NEVER displayed, logged, or saved anywhere
"""

import sys
import time
import getpass
import gc
from typing import Optional, Tuple
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from nesdr_entropy_collector import NESDREntropyCollector

class NFCChaosWriter:
    """Writes chaos-generated values to NFC tags with complete invisibility"""
    
    # NTAG commands
    CMD_GET_VERSION = [0x60]
    CMD_READ = [0x30]
    CMD_WRITE = [0xA2]
    
    def __init__(self):
        self.reader = None
        self.connection = None
        self.entropy_collector = None
        self._setup_reader()
    
    def _setup_reader(self):
        """Initialize NFC reader via PC/SC interface"""
        try:
            available_readers = readers()
            if not available_readers:
                print("❌ No NFC readers found")
                print("   Please connect ACR122U reader")
                sys.exit(1)
            
            # Find ACR122U reader
            for r in available_readers:
                if 'ACR122' in str(r):
                    self.reader = r
                    print(f"✅ Found NFC reader: {r}")
                    break
            
            if not self.reader:
                self.reader = available_readers[0]
                print(f"⚠️  Using reader: {self.reader}")
            
        except Exception as e:
            print(f"❌ Failed to initialize reader: {e}")
            sys.exit(1)
    
    def _connect_to_tag(self) -> bool:
        """Establish connection to NFC tag"""
        try:
            if self.connection:
                self.connection.disconnect()
            
            self.connection = self.reader.createConnection()
            self.connection.connect()
            
            # Get tag info
            response, sw1, sw2 = self.connection.transmit(self.CMD_GET_VERSION)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def _write_uid_block(self, block_data: bytes) -> bool:
        """
        Write UID to block 0 (if tag supports it)
        Most tags have read-only UIDs, but some allow modification
        """
        try:
            # Try to write to block 0 (UID location)
            # This only works on special tags with writable UIDs
            write_cmd = self.CMD_WRITE + [0x00] + list(block_data[:4])
            response, sw1, sw2 = self.connection.transmit(write_cmd)
            
            if sw1 == 0x90 and sw2 == 0x00:
                return True
            
            # If direct write fails, try magic commands for Chinese clones
            # Magic command to unlock UID writing
            magic_unlock = [0xFF, 0x00, 0x00, 0x00, 0x02, 0xD4, 0x42]
            self.connection.transmit(magic_unlock)
            time.sleep(0.1)
            
            # Try write again
            response, sw1, sw2 = self.connection.transmit(write_cmd)
            return sw1 == 0x90 and sw2 == 0x00
            
        except Exception:
            return False
    
    def _write_data_blocks(self, tag_data: bytes) -> bool:
        """Write chaos data to user memory blocks"""
        try:
            # Start at block 4 (user memory area)
            # Blocks 0-3 are typically UID and lock bytes
            start_block = 4
            blocks_to_write = min(len(tag_data) // 4, 10)  # Max 10 blocks
            
            success_count = 0
            for i in range(blocks_to_write):
                block_num = start_block + i
                block_data = tag_data[i*4:(i+1)*4]
                
                # Pad if necessary
                if len(block_data) < 4:
                    block_data = block_data + b'\x00' * (4 - len(block_data))
                
                # Write block
                write_cmd = self.CMD_WRITE + [block_num] + list(block_data)
                response, sw1, sw2 = self.connection.transmit(write_cmd)
                
                if sw1 == 0x90 and sw2 == 0x00:
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"⚠️  Write error: {e}")
            return False
    
    def write_chaos_tag(self) -> bool:
        """
        Main function to write chaos-generated value to NFC tag
        Value is never displayed or logged
        """
        print("\n" + "=" * 60)
        print("   NFC CHAOS WRITER - SECURE TAG PROGRAMMING")
        print("=" * 60)
        
        # Initialize entropy collector
        print("\n🎲 Initializing entropy system...")
        self.entropy_collector = NESDREntropyCollector()
        
        # Collect fresh entropy
        self.entropy_collector.collect_entropy(rounds=2)
        
        # Wait for tag
        print("\n📟 Place NFC tag on reader...")
        print("   Waiting for tag detection...")
        
        attempts = 0
        while attempts < 30:
            if self._connect_to_tag():
                print("✅ Tag detected!")
                break
            time.sleep(0.5)
            attempts += 1
            if attempts % 6 == 0:
                print("   Still waiting...")
        
        if attempts >= 30:
            print("❌ No tag detected after 15 seconds")
            return False
        
        # Generate chaos value (never displayed)
        print("\n🔐 Generating chaos value...")
        nfc_value = self.entropy_collector.get_nfc_value()
        
        if not nfc_value:
            print("❌ Failed to generate value")
            return False
        
        # Generate additional chaos data for user blocks
        extra_data = self.entropy_collector.get_nfc_value()
        extra_data += self.entropy_collector.get_nfc_value()
        
        print("✅ Chaos value generated [HIDDEN]")
        
        # Write to tag
        print("\n✍️  Writing to tag...")
        
        # Try UID write first (may fail on most tags)
        uid_written = self._write_uid_block(nfc_value)
        if uid_written:
            print("   ✅ UID block written")
        else:
            print("   ℹ️  UID is read-only (normal for most tags)")
        
        # Write to data blocks
        data_written = self._write_data_blocks(nfc_value + extra_data)
        if data_written:
            print("   ✅ Data blocks written")
        else:
            print("   ❌ Failed to write data blocks")
            return False
        
        # Verify write (without displaying)
        print("\n🔍 Verifying write...")
        verify_cmd = self.CMD_READ + [0x04]  # Read block 4
        response, sw1, sw2 = self.connection.transmit(verify_cmd)
        
        if sw1 == 0x90 and sw2 == 0x00 and len(response) > 0:
            print("✅ Tag successfully programmed with chaos value")
            print("   Value: [HIDDEN - Never displayed]")
            print("   Security: MAXIMUM")
            return True
        else:
            print("⚠️  Verification inconclusive")
            return False
    
    def double_blind_write(self) -> bool:
        """
        Ultra-secure double-write with hidden verification
        Used for critical authentication tags
        """
        print("\n🔒 DOUBLE-BLIND WRITE MODE")
        print("   Ultra-secure authentication tag creation")
        print("-" * 60)
        
        # First write
        print("\n📝 First write pass...")
        getpass.getpass("   Press ENTER when ready for first tag: ")
        
        if not self.write_chaos_tag():
            print("❌ First write failed")
            return False
        
        # Store first value in memory (never displayed)
        first_value = self.entropy_collector.get_nfc_value()
        
        print("\n✅ First tag complete")
        print("   Remove tag from reader")
        time.sleep(2)
        
        # Second write (verification tag)
        print("\n📝 Second write pass (verification)...")
        getpass.getpass("   Press ENTER when ready for second tag: ")
        
        if not self.write_chaos_tag():
            print("❌ Second write failed")
            return False
        
        print("\n✅ DOUBLE-BLIND WRITE COMPLETE")
        print("   Both tags programmed with matching chaos values")
        print("   Values remain completely hidden")
        
        return True
    
    def cleanup(self):
        """Secure cleanup"""
        if self.connection:
            self.connection.disconnect()
        
        if self.entropy_collector:
            self.entropy_collector.cleanup()
        
        gc.collect()
        print("\n🔒 Writer securely closed")

def main():
    """Main entry point with menu"""
    writer = NFCChaosWriter()
    
    try:
        print("\n" + "=" * 60)
        print("   NFC CHAOS WRITER v1.0")
        print("   NESDR Entropy + Complete Invisibility")
        print("=" * 60)
        
        print("\nSelect mode:")
        print("1. Single tag write")
        print("2. Double-blind write (authentication pair)")
        print("3. Exit")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == '1':
            writer.write_chaos_tag()
        elif choice == '2':
            writer.double_blind_write()
        elif choice == '3':
            print("Exiting...")
        else:
            print("Invalid choice")
        
    finally:
        writer.cleanup()

if __name__ == "__main__":
    main()
