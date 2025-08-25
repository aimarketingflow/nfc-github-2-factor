#!/usr/bin/env python3
"""
Quick RFID Reader Connection Test
Monitors for RFID reader connection and tests capabilities
"""

import serial.tools.list_ports
import time
import sys

def monitor_usb_ports():
    """Monitor for RFID reader connection"""
    print("🔌 RFID Reader Connection Monitor")
    print("=" * 50)
    print("\n📝 Instructions:")
    print("1. Connect your USB RFID reader")
    print("2. The script will detect it automatically")
    print("\nMonitoring USB ports...\n")
    
    known_ports = set()
    
    while True:
        try:
            current_ports = set()
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                current_ports.add(port.device)
                
                # Check if this is a new port
                if port.device not in known_ports:
                    print(f"\n🆕 NEW DEVICE DETECTED!")
                    print(f"   Port: {port.device}")
                    print(f"   Description: {port.description}")
                    if port.vid:
                        print(f"   VID:PID: {port.vid:04X}:{port.pid:04X}")
                    if port.manufacturer:
                        print(f"   Manufacturer: {port.manufacturer}")
                    if port.product:
                        print(f"   Product: {port.product}")
                    
                    # Check if it might be an RFID reader
                    desc_lower = port.description.lower()
                    if any(x in desc_lower for x in ['serial', 'usb', 'uart', 'ch340', 'ftdi', 'cp210']):
                        print("   ✅ Likely an RFID reader!")
                        print("\n   Press Ctrl+C to exit and test this reader")
            
            # Check for disconnected ports
            disconnected = known_ports - current_ports
            for port in disconnected:
                print(f"\n🔌 Device disconnected: {port}")
            
            known_ports = current_ports
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\nExiting monitor...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    monitor_usb_ports()
