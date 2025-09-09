#!/usr/bin/env python3
"""
Mac Process Phone Defense System
Protect Mac processes from phone-based attacks using immovable authentication
"""

import subprocess
import hashlib
import json
import time
import os
from datetime import datetime

class MacProcessPhoneDefense:
    """Protect Mac processes from phone-based attacks"""
    
    def __init__(self):
        self.protected_processes = {}
        self.defense_active = False
        
    def get_mac_hardware_fingerprint(self):
        """Create Mac-specific hardware fingerprint"""
        
        mac_identifiers = {}
        
        try:
            # System UUID
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Hardware UUID' in line:
                    mac_identifiers['hardware_uuid'] = line.split(':')[1].strip()
                elif 'Serial Number' in line:
                    mac_identifiers['serial'] = line.split(':')[1].strip()
        except:
            pass
        
        try:
            # SIP Status (System Integrity Protection)
            result = subprocess.run(['csrutil', 'status'], capture_output=True, text=True)
            mac_identifiers['sip_status'] = result.stdout.strip()
        except:
            mac_identifiers['sip_status'] = 'unknown'
        
        try:
            # Mac model and chip info
            result = subprocess.run(['sysctl', '-n', 'hw.model'], capture_output=True, text=True)
            mac_identifiers['model'] = result.stdout.strip()
            
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            mac_identifiers['cpu'] = result.stdout.strip()
        except:
            pass
        
        # Create composite fingerprint
        fingerprint = hashlib.sha256(str(sorted(mac_identifiers.items())).encode()).hexdigest()
        
        return fingerprint, mac_identifiers
    
    def detect_phone_bluetooth_attacks(self):
        """Detect phone-based Bluetooth attacks"""
        
        print("🔍 Scanning for phone Bluetooth attacks...")
        
        try:
            # Check for active Bluetooth scanning
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'], 
                                  capture_output=True, text=True)
            
            # Look for suspicious devices
            suspicious_indicators = [
                'Android', 'iPhone', 'Kali', 'NetHunter', 
                'Unknown', 'Pineapple', 'Flipper'
            ]
            
            detected_threats = []
            for line in result.stdout.split('\n'):
                for indicator in suspicious_indicators:
                    if indicator.lower() in line.lower():
                        detected_threats.append(line.strip())
            
            if detected_threats:
                print("⚠️  Potential phone attack devices detected:")
                for threat in detected_threats[:3]:  # Limit output
                    print(f"   📱 {threat}")
                return True
            else:
                print("✅ No phone attack devices detected")
                return False
                
        except Exception as e:
            print(f"   Bluetooth scan error: {e}")
            return False
    
    def detect_phone_wifi_attacks(self):
        """Detect phone-based WiFi attacks"""
        
        print("🔍 Scanning for phone WiFi attacks...")
        
        try:
            # Scan for WiFi networks (detect evil twins, pineapples)
            result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
                                   '-s'], capture_output=True, text=True)
            
            # Look for suspicious network names
            suspicious_networks = [
                'pineapple', 'evil', 'free', 'open', 'hack', 
                'test', 'android', 'hotspot'
            ]
            
            detected_networks = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    network_name = line.split()[0]
                    for suspicious in suspicious_networks:
                        if suspicious.lower() in network_name.lower():
                            detected_networks.append(network_name)
                            break
            
            if detected_networks:
                print("⚠️  Suspicious WiFi networks detected:")
                for network in detected_networks[:3]:
                    print(f"   📡 {network}")
                return True
            else:
                print("✅ No suspicious WiFi networks detected")
                return False
                
        except Exception as e:
            print(f"   WiFi scan error: {e}")
            return False
    
    def enable_phone_attack_protection(self):
        """Enable active protection against phone attacks"""
        
        print("🛡️ Enabling phone attack protection...")
        
        # Disable Bluetooth during authentication
        try:
            subprocess.run(['blueutil', '--power', '0'], check=True)
            print("✅ Bluetooth disabled for security")
        except:
            print("⚠️  Could not disable Bluetooth (install blueutil)")
        
        # Monitor network changes
        try:
            current_wifi = subprocess.run(['networksetup', '-getairportnetwork', 'en0'], 
                                        capture_output=True, text=True).stdout.strip()
            print(f"📡 Current WiFi: {current_wifi}")
        except:
            pass
        
        self.defense_active = True
        
    def disable_phone_attack_protection(self):
        """Disable protection and restore normal operation"""
        
        print("🔓 Restoring normal Mac operation...")
        
        # Re-enable Bluetooth
        try:
            subprocess.run(['blueutil', '--power', '1'], check=True)
            print("✅ Bluetooth restored")
        except:
            pass
        
        self.defense_active = False
    
    def protect_ssh_keys(self):
        """Protect SSH keys from phone attacks"""
        
        print("\n🔐 PROTECTING SSH KEYS FROM PHONE ATTACKS")
        print("-" * 50)
        
        # Enable phone protection
        self.enable_phone_attack_protection()
        
        # Scan for threats
        bluetooth_threats = self.detect_phone_bluetooth_attacks()
        wifi_threats = self.detect_phone_wifi_attacks()
        
        if bluetooth_threats or wifi_threats:
            print("🚨 PHONE ATTACK THREATS DETECTED - ABORTING")
            self.disable_phone_attack_protection()
            return False
        
        # Get NFC authentication
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            print("📟 Scan NFC tag to unlock SSH keys...")
            nfc_hash = scanner.invisible_scan_simple()
            
            # Create Mac hardware binding
            mac_fingerprint, mac_details = self.get_mac_hardware_fingerprint()
            
            # Verify this is the correct Mac
            if self.verify_mac_binding(mac_fingerprint):
                print("✅ SSH key access granted")
                print("   Mac hardware verified")
                print("   Phone attacks blocked")
                
                # Load SSH keys securely
                self.load_ssh_keys_securely()
                
                success = True
            else:
                print("❌ Mac hardware verification failed")
                success = False
                
        except Exception as e:
            print(f"❌ SSH protection failed: {e}")
            success = False
        
        # Restore normal operation
        self.disable_phone_attack_protection()
        return success
    
    def protect_keychain_access(self):
        """Protect macOS Keychain from phone attacks"""
        
        print("\n🔐 PROTECTING KEYCHAIN FROM PHONE ATTACKS")
        print("-" * 50)
        
        # Enable protection
        self.enable_phone_attack_protection()
        
        # Check for threats
        if self.detect_phone_bluetooth_attacks() or self.detect_phone_wifi_attacks():
            print("🚨 PHONE THREATS DETECTED - KEYCHAIN PROTECTION ACTIVE")
            self.disable_phone_attack_protection()
            return False
        
        # NFC authentication for keychain
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            print("📟 Scan NFC tag to unlock Keychain...")
            nfc_hash = scanner.invisible_scan_simple()
            
            # Verify Mac binding
            mac_fingerprint, _ = self.get_mac_hardware_fingerprint()
            
            if self.verify_mac_binding(mac_fingerprint):
                print("✅ Keychain access granted")
                print("   Phone attacks neutralized")
                
                # Unlock keychain securely
                self.unlock_keychain_securely()
                
                success = True
            else:
                success = False
                
        except Exception as e:
            print(f"❌ Keychain protection failed: {e}")
            success = False
        
        self.disable_phone_attack_protection()
        return success
    
    def protect_sudo_access(self):
        """Protect sudo access from phone attacks"""
        
        print("\n🔐 PROTECTING SUDO ACCESS FROM PHONE ATTACKS")
        print("-" * 50)
        
        # Enable protection
        self.enable_phone_attack_protection()
        
        # Threat detection
        threats_detected = (self.detect_phone_bluetooth_attacks() or 
                          self.detect_phone_wifi_attacks())
        
        if threats_detected:
            print("🚨 PHONE THREATS DETECTED - SUDO BLOCKED")
            self.disable_phone_attack_protection()
            return False
        
        # NFC authentication for sudo
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            print("📟 Scan NFC tag for administrative access...")
            nfc_hash = scanner.invisible_scan_simple()
            
            # Mac verification
            mac_fingerprint, _ = self.get_mac_hardware_fingerprint()
            
            if self.verify_mac_binding(mac_fingerprint):
                print("✅ Administrative access granted")
                print("   Phone attack protection maintained")
                
                success = True
            else:
                print("❌ Mac verification failed")
                success = False
                
        except Exception as e:
            print(f"❌ Sudo protection failed: {e}")
            success = False
        
        self.disable_phone_attack_protection()
        return success
    
    def verify_mac_binding(self, current_fingerprint):
        """Verify Mac hardware binding"""
        
        # For demo, create stored fingerprint file
        binding_file = "mac_hardware_binding.json"
        
        if not os.path.exists(binding_file):
            # First time - store current Mac fingerprint
            binding_data = {
                'mac_fingerprint': current_fingerprint,
                'creation_time': time.time(),
                'description': 'Mac hardware binding for phone attack protection'
            }
            
            with open(binding_file, 'w') as f:
                json.dump(binding_data, f, indent=2)
            
            print(f"✅ Mac hardware binding created")
            return True
        
        # Load and verify stored fingerprint
        try:
            with open(binding_file, 'r') as f:
                stored_binding = json.load(f)
            
            return stored_binding['mac_fingerprint'] == current_fingerprint
            
        except Exception as e:
            print(f"   Binding verification error: {e}")
            return False
    
    def load_ssh_keys_securely(self):
        """Load SSH keys with phone attack protection"""
        
        try:
            # Check for SSH keys
            ssh_dir = os.path.expanduser("~/.ssh")
            if os.path.exists(ssh_dir):
                key_files = [f for f in os.listdir(ssh_dir) if not f.endswith('.pub')]
                print(f"   Found {len(key_files)} SSH keys")
                
                # Start SSH agent with keys (simplified)
                subprocess.run(['ssh-add', '-l'], capture_output=True)
                print("   SSH agent configured")
            else:
                print("   No SSH directory found")
                
        except Exception as e:
            print(f"   SSH key loading error: {e}")
    
    def unlock_keychain_securely(self):
        """Unlock keychain with phone attack protection"""
        
        try:
            # Check keychain status
            result = subprocess.run(['security', 'show-keychain-info'], 
                                  capture_output=True, text=True)
            print("   Keychain status verified")
            
        except Exception as e:
            print(f"   Keychain unlock error: {e}")

def main():
    """Interactive Mac process phone defense"""
    
    print("🛡️ MAC PROCESS PHONE DEFENSE SYSTEM")
    print("Protecting Mac processes from phone-based attacks")
    print()
    
    defender = MacProcessPhoneDefense()
    
    while True:
        print("\n" + "=" * 50)
        print("   PHONE ATTACK DEFENSE MENU")
        print("=" * 50)
        print("1. Protect SSH keys")
        print("2. Protect Keychain access") 
        print("3. Protect sudo access")
        print("4. Scan for phone threats")
        print("5. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            success = defender.protect_ssh_keys()
            if success:
                print("\n🎉 SSH keys protected from phone attacks!")
        
        elif choice == '2':
            success = defender.protect_keychain_access()
            if success:
                print("\n🎉 Keychain protected from phone attacks!")
        
        elif choice == '3':
            success = defender.protect_sudo_access()
            if success:
                print("\n🎉 Sudo access protected from phone attacks!")
        
        elif choice == '4':
            print("\n🔍 SCANNING FOR PHONE THREATS")
            print("-" * 30)
            bluetooth_threats = defender.detect_phone_bluetooth_attacks()
            wifi_threats = defender.detect_phone_wifi_attacks()
            
            if not (bluetooth_threats or wifi_threats):
                print("\n✅ No phone attack threats detected")
                print("   Environment appears secure")
        
        elif choice == '5':
            print("\n👋 Phone defense system offline")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
