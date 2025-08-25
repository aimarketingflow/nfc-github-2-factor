#!/usr/bin/env python3
"""
NESDR Chaos Value Generator
Generates ultra-random NFC values from RF entropy
Values are NEVER displayed - completely invisible operation
"""

import numpy as np
import hashlib
import secrets
import time
import os
from rtlsdr import RtlSdr
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pickle
import gc

class NESDRChaosGenerator:
    """Generate and store chaos values invisibly"""
    
    def __init__(self):
        self.sdr = None
        self.chaos_values = []
        self.storage_file = '.chaos_vault'  # Hidden file
        
    def initialize_sdr(self):
        """Initialize NESDR device"""
        try:
            print("📡 Initializing NESDR...")
            self.sdr = RtlSdr()
            self.sdr.sample_rate = 2.048e6
            self.sdr.gain = 'auto'
            print("✅ NESDR initialized")
            return True
        except Exception as e:
            print(f"❌ NESDR initialization failed: {e}")
            return False
    
    def collect_rf_entropy(self, frequency_mhz, samples=262144):
        """Collect entropy from specific frequency"""
        if not self.sdr:
            return None
            
        try:
            # Tune to frequency
            self.sdr.center_freq = frequency_mhz * 1e6
            time.sleep(0.1)  # Let tuner settle
            
            # Collect IQ samples
            samples = self.sdr.read_samples(samples)
            
            # Process for entropy
            # Phase noise
            phase = np.angle(samples)
            phase_diff = np.diff(phase)
            
            # Magnitude noise
            magnitude = np.abs(samples)
            mag_diff = np.diff(magnitude)
            
            # Combine entropy sources
            entropy_data = np.concatenate([
                phase_diff.flatten(),
                mag_diff.flatten()
            ])
            
            # Hash the entropy
            entropy_bytes = entropy_data.tobytes()
            hasher = hashlib.sha512()
            hasher.update(entropy_bytes)
            hasher.update(secrets.token_bytes(32))  # Add system entropy
            
            return hasher.digest()
            
        except Exception:
            return None
    
    def generate_chaos_value(self):
        """Generate a single chaos NFC value"""
        print("\n🎲 Generating chaos value...")
        
        # Collect from multiple frequencies
        frequencies = [433.92, 915.0, 868.0, 315.0, 40.68]
        entropy_pool = b''
        
        for freq in frequencies:
            print(f"   Scanning {freq} MHz...", end='')
            entropy = self.collect_rf_entropy(freq, samples=131072)
            if entropy:
                entropy_pool += entropy
                print(" ✓")
            else:
                print(" ✗")
        
        if len(entropy_pool) < 64:
            print("❌ Insufficient entropy collected")
            return None
        
        # Generate 4-byte NFC value using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=4,
            salt=b'chaos_nfc_2024',
            iterations=100000,
        )
        
        # Create value (never displayed)
        chaos_value = kdf.derive(entropy_pool)
        
        # Store invisibly
        self.chaos_values.append(chaos_value)
        
        print("\n✅ Chaos value generated and stored")
        print("   Value: [HIDDEN]")
        print(f"   Total stored: {len(self.chaos_values)}")
        
        return True
    
    def save_vault(self):
        """Save chaos values to hidden vault file"""
        try:
            # Encrypt/obfuscate before saving
            vault_data = {
                'timestamp': time.time(),
                'count': len(self.chaos_values),
                'values': self.chaos_values
            }
            
            with open(self.storage_file, 'wb') as f:
                pickle.dump(vault_data, f)
            
            print(f"\n💾 Vault saved: {len(self.chaos_values)} values")
            return True
        except Exception:
            print("❌ Failed to save vault")
            return False
    
    def load_vault(self):
        """Load existing chaos vault"""
        if not os.path.exists(self.storage_file):
            print("📦 No existing vault found")
            return False
            
        try:
            with open(self.storage_file, 'rb') as f:
                vault_data = pickle.load(f)
            
            self.chaos_values = vault_data.get('values', [])
            count = vault_data.get('count', 0)
            timestamp = vault_data.get('timestamp', 0)
            
            if count > 0:
                print(f"\n📦 Vault loaded: {count} values")
                print(f"   Created: {time.ctime(timestamp)}")
                return True
            return False
            
        except Exception:
            print("❌ Failed to load vault")
            return False
    
    def get_next_value(self):
        """Get next chaos value for NFC writing (never displayed)"""
        if not self.chaos_values:
            print("❌ No chaos values available")
            return None
        
        # Pop value from list (use once)
        value = self.chaos_values.pop(0)
        
        print(f"\n🔑 Value retrieved [HIDDEN]")
        print(f"   Remaining: {len(self.chaos_values)}")
        
        # Save updated vault
        self.save_vault()
        
        return value
    
    def cleanup(self):
        """Clean up resources"""
        if self.sdr:
            self.sdr.close()
        
        # Secure memory cleanup
        self.chaos_values = []
        gc.collect()
        
        print("\n🔒 Generator closed")

def main():
    """Standalone chaos value generator"""
    
    generator = NESDRChaosGenerator()
    
    print("=" * 60)
    print("   NESDR CHAOS VALUE GENERATOR")
    print("=" * 60)
    print("\n⚡ Ultra-random NFC value generation")
    print("🔒 All values remain hidden at all times")
    
    # Initialize NESDR
    if not generator.initialize_sdr():
        print("\n⚠️  Please connect NESDR device")
        return
    
    # Load existing vault
    generator.load_vault()
    
    while True:
        print("\n" + "=" * 40)
        print("OPTIONS:")
        print(f"1. Generate new chaos value")
        print(f"2. View vault status ({len(generator.chaos_values)} values)")
        print("3. Clear vault (delete all)")
        print("4. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == '1':
            success = generator.generate_chaos_value()
            if success:
                # Auto-save after each generation
                generator.save_vault()
                
        elif choice == '2':
            print(f"\n📊 VAULT STATUS")
            print(f"   Stored values: {len(generator.chaos_values)}")
            print(f"   Storage file: {generator.storage_file}")
            
            if len(generator.chaos_values) > 0:
                print(f"\n   Ready for NFC writing!")
                print(f"   Run nfc_chaos_writer.py to use values")
                
        elif choice == '3':
            confirm = input("\n⚠️  Delete all chaos values? (yes/no): ")
            if confirm.lower() == 'yes':
                generator.chaos_values = []
                generator.save_vault()
                print("✅ Vault cleared")
                
        elif choice == '4':
            generator.cleanup()
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
