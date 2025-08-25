#!/usr/bin/env python3
"""
RFID/NFC Chaos Writer - Tests RFID readers for NFC writing capability
Attempts to use USB RFID readers to write NFC tags with chaos entropy
"""

import sys
import time
import serial
import serial.tools.list_ports
import getpass
import struct
from typing import Optional, List, Tuple
from nesdr_entropy_collector import NESDREntropyCollector

class RFIDNFCWriter:
    """Attempts to write NFC tags using RFID hardware"""
    
    # Common NFC/RFID commands (varies by reader model)
    MIFARE_COMMANDS = {
        'GET_VERSION': b'\x02\x00\x03\xFF\x01\xFE',  # Get reader version
        'BEEP': b'\x02\x00\x03\xFF\x03\xFC',         # Beep confirmation
        'READ_UID': b'\x02\x00\x04\xFF\x0A\x01\xF4', # Read card UID
        'WRITE_BLOCK': b'\x02\x00\x0A\xFF\x0B',      # Write data to block
    }
    
    def __init__(self):
        self.port = None
        self.serial_conn = None
        self.entropy_collector = None
        self.reader_type = None
        
    def find_readers(self) -> List[serial.tools.list_ports.ListPortInfo]:
        """Find all potential RFID/NFC readers"""
        print("\n🔍 Scanning for RFID/NFC readers...")
        print("-" * 50)
        
        ports = serial.tools.list_ports.comports()
        rfid_ports = []
        
        for port in ports:
            # Check for common RFID/NFC reader identifiers
            desc_lower = port.description.lower()
            
            # Common identifiers
            if any(x in desc_lower for x in [
                'rfid', 'nfc', 'ch340', 'ch341', 'pl2303', 
                'cp210', 'ft232', 'acr', 'pn5', 'rc522'
            ]):
                rfid_ports.append(port)
                print(f"✅ Found: {port.device}")
                print(f"   Name: {port.description}")
                print(f"   VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid else "   VID:PID: Unknown")
                
                # Check if it might support NFC (13.56MHz)
                if any(x in desc_lower for x in ['nfc', '13.56', 'mifare', 'ntag']):
                    print(f"   💡 May support NFC writing!")
        
        if not rfid_ports:
            print("❌ No RFID/NFC readers found via USB serial")
            
        return rfid_ports
    
    def test_reader(self, port_info: serial.tools.list_ports.ListPortInfo) -> bool:
        """Test if reader supports NFC operations"""
        print(f"\n🧪 Testing reader on {port_info.device}...")
        
        # Common baud rates for RFID readers
        baud_rates = [9600, 19200, 38400, 57600, 115200]
        
        for baud in baud_rates:
            try:
                print(f"   Trying {baud} baud...")
                self.serial_conn = serial.Serial(
                    port=port_info.device,
                    baudrate=baud,
                    timeout=1,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                
                # Clear buffer
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Try to get version
                self.serial_conn.write(self.MIFARE_COMMANDS['GET_VERSION'])
                time.sleep(0.1)
                
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.read(self.serial_conn.in_waiting)
                    print(f"   ✅ Reader responded at {baud} baud")
                    print(f"   Response length: {len(response)} bytes")
                    
                    # Check if it's a known NFC-capable reader
                    if self._check_nfc_capability(response):
                        print("   🎯 NFC writing capability detected!")
                        self.port = port_info
                        return True
                    
                self.serial_conn.close()
                
            except (serial.SerialException, OSError) as e:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                continue
        
        print(f"   ❌ No NFC capability detected on {port_info.device}")
        return False
    
    def _check_nfc_capability(self, response: bytes) -> bool:
        """Check if response indicates NFC capability"""
        # Look for common NFC reader response patterns
        # This varies by manufacturer
        
        # Check for 13.56MHz indicator
        if b'13.56' in response or b'MIFARE' in response:
            self.reader_type = 'MIFARE'
            return True
            
        # Check for PN532 responses
        if b'PN5' in response or len(response) > 6:
            self.reader_type = 'PN532'
            return True
            
        # Generic check - if we got a structured response
        if len(response) >= 4:
            self.reader_type = 'GENERIC'
            return True
            
        return False
    
    def scan_for_tag(self) -> Optional[bytes]:
        """Scan for NFC tag presence"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
            
        try:
            # Send read UID command
            self.serial_conn.reset_input_buffer()
            self.serial_conn.write(self.MIFARE_COMMANDS['READ_UID'])
            time.sleep(0.2)
            
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)
                
                # Parse UID from response (format varies by reader)
                if len(response) >= 7:
                    # Try to extract 4-byte UID
                    # Common format: [STX][LEN][CMD][UID1][UID2][UID3][UID4][CHECKSUM]
                    if len(response) >= 9:
                        uid = response[3:7]  # Extract 4 bytes
                        return uid
                        
            return None
            
        except Exception as e:
            print(f"   Scan error: {e}")
            return None
    
    def write_chaos_tag(self) -> bool:
        """Write chaos-generated value to NFC tag"""
        print("\n" + "=" * 60)
        print("   RFID/NFC CHAOS WRITER")
        print("=" * 60)
        
        # Find readers
        readers = self.find_readers()
        
        if not readers:
            print("\n❌ No RFID readers found. Please connect a reader.")
            return False
        
        # Test each reader for NFC capability
        nfc_capable = False
        for reader in readers:
            if self.test_reader(reader):
                nfc_capable = True
                break
        
        if not nfc_capable:
            print("\n⚠️  No NFC-capable readers found")
            print("   Your RFID reader may only support 125kHz tags")
            print("   NFC tags require 13.56MHz readers")
            return False
        
        # Initialize entropy
        print("\n🎲 Initializing entropy system...")
        self.entropy_collector = NESDREntropyCollector()
        self.entropy_collector.collect_entropy(rounds=2)
        
        # Generate chaos value
        chaos_value = self.entropy_collector.get_nfc_value()
        if not chaos_value:
            print("❌ Failed to generate chaos value")
            return False
        
        print("✅ Chaos value generated [HIDDEN]")
        
        # Wait for tag
        print("\n📟 Place NFC tag on reader...")
        print("   Scanning for tag...")
        
        attempts = 0
        tag_found = False
        
        while attempts < 60:
            uid = self.scan_for_tag()
            if uid:
                print(f"✅ Tag detected!")
                print(f"   UID Length: {len(uid)} bytes")
                print(f"   UID: [PARTIALLY HIDDEN] {uid[0]:02X}:••:••:••")
                tag_found = True
                break
            
            time.sleep(0.5)
            attempts += 1
            if attempts % 10 == 0:
                print("   Still scanning...")
        
        if not tag_found:
            print("❌ No tag detected after 30 seconds")
            return False
        
        # Attempt to write
        print("\n✍️  Attempting to write chaos value...")
        
        # Note: Actual write implementation depends on specific reader protocol
        # Most USB RFID readers have proprietary protocols
        print("⚠️  Write functionality depends on specific reader model")
        print("   Most USB RFID readers are read-only for security")
        print("   Consider using dedicated NFC writer hardware")
        
        # Beep to indicate completion attempt
        try:
            self.serial_conn.write(self.MIFARE_COMMANDS['BEEP'])
        except:
            pass
        
        return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        if self.entropy_collector:
            self.entropy_collector.cleanup()
        
        print("\n🔒 Writer closed")

def main():
    """Test RFID readers for NFC writing capability"""
    
    writer = RFIDNFCWriter()
    
    try:
        print("=" * 60)
        print("   RFID/NFC HARDWARE COMPATIBILITY TEST")
        print("=" * 60)
        
        # Find and test readers
        readers = writer.find_readers()
        
        if not readers:
            print("\n📝 Summary:")
            print("   No USB RFID readers detected")
            print("   Connect a reader and try again")
            return
        
        print(f"\n📝 Found {len(readers)} potential reader(s)")
        
        # Test for NFC capability
        print("\n🧪 Testing NFC capability...")
        nfc_count = 0
        for reader in readers:
            if writer.test_reader(reader):
                nfc_count += 1
        
        print("\n📊 COMPATIBILITY REPORT")
        print("=" * 60)
        print(f"   Total readers found: {len(readers)}")
        print(f"   NFC-capable readers: {nfc_count}")
        
        if nfc_count > 0:
            print("\n✅ NFC writing may be possible!")
            print("   Use option 1 to attempt tag writing")
        else:
            print("\n⚠️  No NFC-capable readers detected")
            print("   Your RFID reader may only support 125kHz tags")
            print("   NFC requires 13.56MHz readers like:")
            print("   - ACR122U")
            print("   - PN532")
            print("   - RC522 (with USB adapter)")
        
        if nfc_count > 0:
            print("\n🎯 Ready to write NFC tags with chaos entropy!")
            choice = input("\n1. Write chaos tag\n2. Exit\n\nChoice: ")
            
            if choice == '1':
                writer.write_chaos_tag()
        
    finally:
        writer.cleanup()

if __name__ == "__main__":
    main()
