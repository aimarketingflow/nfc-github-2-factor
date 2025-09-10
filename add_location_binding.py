#!/usr/bin/env python3
"""
Add Location Binding to Existing Authentication Pack
Updates current auth pack with USB hardware fingerprinting
"""

import json
import hashlib
import logging
import os
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_usb_hardware_fingerprint(usb_path):
    """Get unique hardware fingerprint of USB device"""
    
    try:
        result = subprocess.run(['system_profiler', 'SPUSBDataType', '-json'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            return None, None
        
        usb_data = json.loads(result.stdout)
        volume_name = os.path.basename(usb_path)
        
        def find_usb_device(items, target_volume):
            for item in items:
                if 'volumes' in item:
                    for volume in item['volumes']:
                        if volume.get('mount_point', '').endswith(target_volume):
                            return item
                if '_items' in item:
                    result = find_usb_device(item['_items'], target_volume)
                    if result:
                        return result
            return None
        
        usb_device = find_usb_device(usb_data.get('SPUSBDataType', []), volume_name)
        
        if not usb_device:
            fingerprint_data = {
                'volume_name': volume_name,
                'mount_point': usb_path,
                'fallback': True,
                'timestamp': datetime.now().isoformat()
            }
        else:
            fingerprint_data = {
                'product_id': usb_device.get('product_id', 'unknown'),
                'vendor_id': usb_device.get('vendor_id', 'unknown'),
                'serial_num': usb_device.get('serial_num', 'unknown'),
                'manufacturer': usb_device.get('manufacturer', 'unknown'),
                'location_id': usb_device.get('location_id', 'unknown'),
                'volume_name': volume_name,
                'mount_point': usb_path,
                'timestamp': datetime.now().isoformat()
            }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        hardware_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        return hardware_hash, fingerprint_data
        
    except Exception as e:
        logging.error(f"Failed to get USB fingerprint: {e}")
        return None, None

def add_location_binding():
    """Add location binding to existing authentication pack"""
    
    usb_path = '/Volumes/BLUESAM'
    auth_pack_path = os.path.join(usb_path, 'mobileshield_auth_pack.json')
    
    if not os.path.exists(auth_pack_path):
        print("❌ No authentication pack found")
        return False
    
    # Get USB hardware fingerprint
    hardware_hash, fingerprint_data = get_usb_hardware_fingerprint(usb_path)
    if not hardware_hash:
        print("❌ Could not get USB hardware fingerprint")
        return False
    
    # Load existing auth pack
    with open(auth_pack_path, 'r') as f:
        pack_data = json.load(f)
    
    # Backup original
    backup_path = os.path.join(usb_path, 'mobileshield_auth_pack_pre_binding.json')
    with open(backup_path, 'w') as f:
        json.dump(pack_data, f, indent=2)
    
    # Add location binding
    pack_data['location_binding'] = {
        'hardware_fingerprint': hardware_hash,
        'hardware_details': fingerprint_data,
        'binding_timestamp': datetime.now().isoformat(),
        'binding_version': '1.0',
        'security_note': 'USB hardware binding prevents data theft/movement'
    }
    
    # Update pack metadata
    pack_data['pack_metadata']['location_bound'] = True
    pack_data['pack_metadata']['security_level'] = 'hardware_bound'
    
    # Add to authentication requirements
    if 'authentication_requirements' in pack_data:
        pack_data['authentication_requirements'].append('USB hardware fingerprint verification')
    
    # Save updated pack
    with open(auth_pack_path, 'w') as f:
        json.dump(pack_data, f, indent=2)
    
    print("✅ Location binding added successfully!")
    print(f"   Hardware fingerprint: {hardware_hash[:16]}...")
    print(f"   USB details: {fingerprint_data.get('manufacturer', 'unknown')}")
    print(f"   Backup saved: {backup_path}")
    
    return True

if __name__ == "__main__":
    add_location_binding()
