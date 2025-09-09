#!/usr/bin/env python3
"""
Debug USB Fingerprint Calculation
Compare fingerprints between capture and auth systems
"""

import subprocess
import hashlib
import os

def debug_usb_fingerprint(usb_path):
    """Debug USB fingerprint calculation"""
    
    print(f"🔍 DEBUGGING USB FINGERPRINT")
    print(f"   USB Path: {usb_path}")
    print("=" * 40)
    
    try:
        result = subprocess.run(['diskutil', 'info', usb_path], 
                              capture_output=True, text=True)
        
        print("📋 Raw diskutil output:")
        print(result.stdout)
        print("=" * 40)
        
        # Parse info like capture system does
        usb_info_capture = {}
        for line in result.stdout.split('\n'):
            if 'Volume UUID' in line:
                usb_info_capture['volume_uuid'] = line.split(':')[1].strip()
            elif 'Device / Media Name' in line:
                usb_info_capture['device_name'] = line.split(':')[1].strip()
            elif 'Total Size' in line:
                usb_info_capture['total_size'] = line.split(':')[1].strip()
            elif 'File System Personality' in line:
                usb_info_capture['filesystem'] = line.split(':')[1].strip()
        
        usb_info_capture['mount_point'] = usb_path
        usb_info_capture['creation_time'] = os.path.getmtime(usb_path)
        
        print("🎯 CAPTURE SYSTEM INFO:")
        for key, value in usb_info_capture.items():
            print(f"   {key}: {value}")
        
        # Calculate capture fingerprint
        fingerprint_data_capture = str(sorted(usb_info_capture.items()))
        fingerprint_capture = hashlib.sha256(fingerprint_data_capture.encode()).hexdigest()
        
        print(f"\n🔒 CAPTURE FINGERPRINT: {fingerprint_capture}")
        
        # Parse info like auth system does  
        usb_info_auth = {}
        for line in result.stdout.split('\n'):
            if 'Volume UUID' in line:
                usb_info_auth['volume_uuid'] = line.split(':')[1].strip()
            elif 'Mount Point' in line:
                usb_info_auth['mount_point'] = line.split(':')[1].strip()
            elif 'Device / Media Name' in line:
                usb_info_auth['device_name'] = line.split(':')[1].strip()
        
        print(f"\n🎯 AUTH SYSTEM INFO:")
        for key, value in usb_info_auth.items():
            print(f"   {key}: {value}")
        
        # Calculate auth fingerprint
        fingerprint_data_auth = str(sorted(usb_info_auth.items()))
        fingerprint_auth = hashlib.sha256(fingerprint_data_auth.encode()).hexdigest()
        
        print(f"\n🔒 AUTH FINGERPRINT: {fingerprint_auth}")
        
        print(f"\n⚡ COMPARISON:")
        print(f"   Match: {'✅ YES' if fingerprint_capture == fingerprint_auth else '❌ NO'}")
        
        if fingerprint_capture != fingerprint_auth:
            print(f"\n🐛 MISMATCH DETAILS:")
            print(f"   Capture data: {fingerprint_data_capture}")
            print(f"   Auth data: {fingerprint_data_auth}")
        
        return fingerprint_capture, fingerprint_auth
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        return None, None

def main():
    """Debug USB fingerprint"""
    
    usb_path = "/Volumes/SILVER"
    debug_usb_fingerprint(usb_path)

if __name__ == "__main__":
    main()
