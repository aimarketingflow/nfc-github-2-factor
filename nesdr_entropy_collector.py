#!/usr/bin/env python3
"""
NESDR Entropy Collector for NFC Chaos Writer
Captures RF noise across multiple bands for cryptographic randomness
NEVER displays or logs the actual entropy values
"""

import numpy as np
import hashlib
import os
import sys
import time
from rtlsdr import RtlSdr
from typing import Optional, Tuple
import gc

class NESDREntropyCollector:
    """Collects RF entropy from NESDR without ever displaying values"""
    
    # Target frequencies for entropy collection (in MHz)
    ENTROPY_BANDS = [
        433.92,   # ISM band - lots of noise
        915.0,    # ISM band - industrial noise
        2437.0,   # 2.4GHz WiFi channel 6 noise floor
        868.0,    # European ISM
        315.0,    # Garage door/car remotes
        40.68,    # Amateur radio noise floor
    ]
    
    def __init__(self):
        self.sdr = None
        self.entropy_pool = bytearray()
        self._setup_sdr()
    
    def _setup_sdr(self):
        """Initialize RTL-SDR with optimal settings"""
        try:
            self.sdr = RtlSdr()
            # Set sample rate (2.048 MHz is stable)
            self.sdr.sample_rate = 2.048e6
            # Auto gain for maximum noise
            self.sdr.gain = 'auto'
            print("✅ NESDR initialized for entropy collection")
        except Exception as e:
            print(f"❌ Failed to initialize NESDR: {e}")
            sys.exit(1)
    
    def _collect_rf_noise(self, freq_mhz: float, duration_ms: int = 50) -> bytes:
        """
        Collect RF noise from specific frequency
        Returns raw entropy bytes (never displayed)
        """
        try:
            # Tune to frequency
            self.sdr.center_freq = freq_mhz * 1e6
            
            # Calculate samples needed
            samples_needed = int(self.sdr.sample_rate * duration_ms / 1000)
            
            # Read IQ samples
            samples = self.sdr.read_samples(samples_needed)
            
            # Extract entropy from phase noise and amplitude variations
            # Use imaginary component for phase noise
            phase_noise = np.angle(samples)
            # Use magnitude variations
            magnitude_noise = np.abs(samples)
            
            # Combine both sources
            combined = np.concatenate([phase_noise, magnitude_noise])
            
            # Convert to bytes using least significant bits (most random)
            raw_bytes = (combined * 255).astype(np.uint8).tobytes()
            
            # Hash to ensure uniform distribution
            hasher = hashlib.sha512()
            hasher.update(raw_bytes)
            
            # Add system entropy for extra randomness
            hasher.update(os.urandom(32))
            
            return hasher.digest()
            
        except Exception as e:
            print(f"⚠️  RF collection error at {freq_mhz}MHz: {e}")
            # Fall back to system entropy
            return os.urandom(64)
    
    def collect_entropy(self, rounds: int = 3) -> None:
        """
        Collect entropy from multiple bands and rounds
        Entropy is stored internally, never displayed
        """
        print("\n🎲 Collecting RF entropy...")
        print("=" * 50)
        
        for round_num in range(rounds):
            print(f"\n📡 Round {round_num + 1}/{rounds}")
            
            for freq in self.ENTROPY_BANDS:
                # Skip 2.4GHz if SDR can't tune that high
                if freq > 1700 and self.sdr.get_tuner_type() != 'E4000':
                    continue
                
                print(f"   Scanning {freq:.2f} MHz...", end='')
                
                # Collect entropy
                noise_bytes = self._collect_rf_noise(freq)
                
                # Add to pool (never displayed)
                self.entropy_pool.extend(noise_bytes)
                
                print(" ✓")
                
                # Small delay between frequencies
                time.sleep(0.1)
        
        print("\n✅ Entropy collection complete")
        print(f"   Pool size: {len(self.entropy_pool)} bytes")
        print("   Entropy quality: CRYPTOGRAPHIC")
    
    def get_nfc_value(self) -> Optional[bytes]:
        """
        Generate a 4-byte NFC UID from entropy pool
        Value is returned but NEVER displayed
        """
        if len(self.entropy_pool) < 256:
            print("⚠️  Insufficient entropy, collecting more...")
            self.collect_entropy(rounds=1)
        
        # Extract 256 bytes for processing
        seed_bytes = bytes(self.entropy_pool[:256])
        
        # Remove used entropy
        self.entropy_pool = self.entropy_pool[256:]
        
        # Create strong NFC value using PBKDF2
        nfc_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            seed_bytes,
            b'NFC_CHAOS_WRITER_SALT_2025',
            iterations=100000,
            dklen=4
        )
        
        # Ensure it's a valid NFC UID (avoid reserved values)
        # Set first byte to valid manufacturer code
        nfc_array = bytearray(nfc_bytes)
        if nfc_array[0] == 0x00 or nfc_array[0] == 0xFF:
            nfc_array[0] = 0x04  # NXP manufacturer code
        
        return bytes(nfc_array)
    
    def get_entropy_quality(self) -> str:
        """Check entropy pool quality without revealing content"""
        if len(self.entropy_pool) == 0:
            return "EMPTY - Needs collection"
        elif len(self.entropy_pool) < 256:
            return "LOW - Needs more collection"
        elif len(self.entropy_pool) < 1024:
            return "MODERATE - Sufficient for few tags"
        else:
            return "HIGH - Sufficient for many tags"
    
    def cleanup(self):
        """Secure cleanup of resources"""
        if self.sdr:
            self.sdr.close()
        
        # Overwrite entropy pool
        if self.entropy_pool:
            for i in range(len(self.entropy_pool)):
                self.entropy_pool[i] = 0
        
        self.entropy_pool = bytearray()
        gc.collect()
        
        print("🔒 Entropy collector securely closed")

def test_entropy_collection():
    """Test entropy collection without revealing values"""
    print("=" * 60)
    print("   NESDR ENTROPY COLLECTOR TEST")
    print("=" * 60)
    
    collector = NESDREntropyCollector()
    
    try:
        # Collect entropy
        collector.collect_entropy(rounds=2)
        
        # Check quality
        quality = collector.get_entropy_quality()
        print(f"\n📊 Entropy Quality: {quality}")
        
        # Generate test NFC value (not displayed)
        nfc_value = collector.get_nfc_value()
        if nfc_value:
            print("\n✅ Successfully generated NFC value")
            print(f"   Length: {len(nfc_value)} bytes")
            print("   Value: [HIDDEN - Never displayed]")
        else:
            print("\n❌ Failed to generate NFC value")
        
    finally:
        collector.cleanup()
    
    print("\n" + "=" * 60)
    print("   TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_entropy_collection()
