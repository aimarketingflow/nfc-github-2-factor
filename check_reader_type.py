#!/usr/bin/env python3
"""
Check what type of RFID/NFC reader is connected
"""

from smartcard.System import readers
import serial.tools.list_ports

def check_readers():
    print("🔍 READER DETECTION REPORT")
    print("=" * 50)
    
    # Check PC/SC readers (NFC writers)
    pcsc_readers = readers()
    print(f"\n📟 PC/SC Readers (NFC Write Capable): {len(pcsc_readers)}")
    
    if pcsc_readers:
        for i, reader in enumerate(pcsc_readers):
            print(f"   {i+1}. {reader}")
            if 'ACR122' in str(reader):
                print("      ✅ This can write NFC tags!")
    else:
        print("   ❌ No NFC writers found")
    
    # Check USB serial devices (RFID readers)
    serial_ports = serial.tools.list_ports.comports()
    print(f"\n🔌 USB Serial Devices: {len(serial_ports)}")
    
    for port in serial_ports:
        print(f"   {port.device}: {port.description}")
        if any(x in port.description.lower() for x in ['ch340', 'uart', 'serial']):
            print("      💡 Might be an RFID reader (read-only)")
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("-" * 30)
    
    if pcsc_readers:
        print("✅ You have NFC writing capability!")
    else:
        print("❌ No NFC writers detected")
        print("\n💡 To write NFC tags with chaos values:")
        print("   • Get ACR122U NFC reader ($30-40)")
        print("   • Or PN532 module with USB adapter")
        print("   • Current reader likely read-only")

if __name__ == "__main__":
    check_readers()
