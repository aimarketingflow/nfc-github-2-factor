#!/usr/bin/env python3
"""
Create Mock Chaos Vault - Generate fake chaos values for testing without hardware
Creates a .chaos_vault file with mock entropy data for NFC GitHub testing
"""

import os
import pickle
import time
import secrets
import hashlib

def generate_mock_chaos_values(count=50):
    """Generate mock chaos values using system entropy"""
    print(f"🎲 Generating {count} mock chaos values...")
    
    chaos_values = []
    
    for i in range(count):
        # Generate 4 bytes of cryptographically secure random data
        # This simulates what would come from NESDR RF sampling
        mock_entropy = secrets.token_bytes(32)  # 32 bytes raw entropy
        
        # Hash down to 4 bytes like real chaos generator
        chaos_hash = hashlib.sha256(mock_entropy).digest()[:4]
        chaos_values.append(chaos_hash)
        
        if (i + 1) % 10 == 0:
            print(f"   Generated {i + 1}/{count} values...")
    
    return chaos_values

def save_mock_vault(chaos_values):
    """Save mock vault to disk"""
    vault_data = {
        'timestamp': time.time(),
        'count': len(chaos_values),
        'values': chaos_values,
        'source': 'MOCK_GENERATOR',
        'mock': True
    }
    
    storage_file = '.chaos_vault'
    
    try:
        with open(storage_file, 'wb') as f:
            pickle.dump(vault_data, f)
        
        print(f"💾 Mock vault saved: {storage_file}")
        print(f"   Values: {len(chaos_values)}")
        print(f"   Source: MOCK (for testing)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save vault: {e}")
        return False

def main():
    """Create mock chaos vault for testing"""
    
    print("=" * 60)
    print("   MOCK CHAOS VAULT GENERATOR")
    print("=" * 60)
    print("\n🧪 Creating mock vault for testing NFC GitHub system")
    print("   (Simulates NESDR chaos generation without hardware)")
    
    # Check if vault already exists
    if os.path.exists('.chaos_vault'):
        choice = input("\n⚠️  Vault already exists. Overwrite? (y/n): ")
        if choice.lower() != 'y':
            print("   Cancelled.")
            return
    
    # Generate mock values
    chaos_values = generate_mock_chaos_values(50)
    
    # Save vault
    if save_mock_vault(chaos_values):
        print("\n✅ Mock vault created successfully!")
        print("\n📋 You can now test:")
        print("   python3 simple_verify_test.py")
        print("   python3 nfc_writer_test.py (hardware required)")
        print("   python3 nfc_chaos_verifier.py")
    else:
        print("\n❌ Failed to create mock vault")

if __name__ == "__main__":
    main()
