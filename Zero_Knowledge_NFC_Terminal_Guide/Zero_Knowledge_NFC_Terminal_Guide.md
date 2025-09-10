# Zero-Knowledge NFC Authentication Terminal Guide

## Overview
Complete zero-knowledge NFC authentication system for GitHub SSH with real ambient audio and EMF data capture.

## Quick Start Commands

### 1. Create Authentication Pack (Real Ambient Data)
```bash
cd /path/to/your/project/NFC\ Security\ Builds/GitHub_Integration/NFC_GitHub_2FA_v2
source venv_nfc_github/bin/activate
python3 real_ambient_zero_knowledge_auth.py
# Choose option 1
```

### 2. Authenticate with Dual NFC Scans
```bash
cd /path/to/your/project/NFC\ Security\ Builds/GitHub_Integration/NFC_GitHub_2FA_v2
source venv_nfc_github/bin/activate
python3 real_ambient_zero_knowledge_auth.py
# Choose option 2
```

## System Components

### Zero-Knowledge Features
- **NFC Masking**: Raw NFC data displayed as `**********`
- **Immediate Hashing**: NFC values hashed instantly, never stored
- **Memory Clearing**: All sensitive data overwritten after use
- **Invisible Passphrase**: Generated and used without display

### Real Ambient Data Capture
- **Audio**: 60 seconds of ambient microphone data (2.3MB typical)
- **EMF**: 10 seconds of NESDR RF spectrum capture (40MB typical)
- **Encryption**: Combined ambient data encrypted with NFC unlock key
- **Fallback**: System generates entropy-based EMF if NESDR unavailable

### Dual NFC Scan Process
1. **First Scan**: Unlocks encrypted ambient data from USB
2. **Second Scan**: Combines with ambient data for passphrase assembly
3. **SSH Generation**: Creates encrypted SSH key with invisible passphrase

## File Locations

### Generated SSH Keys
```
~/.ssh/github_real_ambient_[timestamp]     # Private key (encrypted)
~/.ssh/github_real_ambient_[timestamp].pub # Public key
```

### USB Authentication Pack
```
/Volumes/YOUR_USB_DRIVE/real_ambient_auth/real_ambient_pack.json        # Pack metadata
/Volumes/YOUR_USB_DRIVE/real_ambient_auth/encrypted_ambient_[timestamp].dat # Encrypted ambient data
```

## Security Model

### Zero-Knowledge Guarantees
- NFC tag UIDs never displayed or stored in plaintext
- Passphrase never displayed or stored anywhere
- Raw ambient data encrypted immediately after capture
- All sensitive variables overwritten before function exit

### Multi-Factor Authentication
1. **Physical USB**: Hardware fingerprinting and location binding
2. **NFC Tag**: Cryptographic unlock key and passphrase component
3. **Ambient Audio**: Environmental fingerprint (60 seconds)
4. **Ambient EMF**: RF spectrum fingerprint (10 seconds)

### Attack Resistance
- **USB Theft**: Ambient data encrypted, unusable without NFC
- **NFC Cloning**: Requires physical USB with matching ambient data
- **Replay Attacks**: Ambient data changes over time
- **Side Channel**: No sensitive data displayed or logged

## Troubleshooting

### NESDR EMF Capture Issues
```bash
# Check NESDR dongle
rtl_test -t

# If not found, system uses entropy-based fallback EMF data
```

### Audio Capture Issues
```bash
# Check microphone permissions in System Preferences > Security & Privacy
# Ensure ffmpeg has microphone access
```

### Terminal Issues
```bash
# If NFC scanning hangs, the system includes 30-second timeout
# Press Ctrl+C to cancel if needed
```

## Example Session

```
🔐 Real Ambient Zero-Knowledge NFC Authentication
==================================================
Choose:
(1) Create pack with real ambient audio + EMF
(2) Authenticate with dual NFC scans + real ambient

Enter choice (1 or 2): 1

🔐 CREATING REAL AMBIENT ZERO-KNOWLEDGE PACK
==================================================
✅ Found USB: /Volumes/YOUR_USB_DRIVE

🏷️ STEP 1: NFC UNLOCK KEY BINDING
🏷️  NFC SCAN - UNLOCK KEY BINDING
🔒 Place NFC tag on reader...
   ⚡ ZERO-KNOWLEDGE MODE - input will be masked
   🎯 Scan NFC tag now (press Enter when done):
**********
✅ NFC scan completed (zero-knowledge mode)
✅ NFC unlock key bound (never stored)

🎵 STEP 2: REAL AMBIENT AUDIO CAPTURE
🎵 Capturing ambient audio (60 seconds)...
   Progress: ●●●●●●●●●●●●
✅ Ambient audio captured: 2302014 bytes

📡 STEP 3: AMBIENT EMF CAPTURE
📡 Capturing ambient EMF data...
   Progress: 📡 NESDR dongle detected, capturing RF spectrum...
●●●●●●●●●●
✅ Ambient EMF captured: 40960000 bytes

🔐 STEP 4: ENCRYPTING AMBIENT DATA
✅ Real ambient data encrypted with NFC unlock key

💾 STEP 5: SAVING AUTHENTICATION PACK
   📁 Pack saved: /Volumes/YOUR_USB_DRIVE/real_ambient_auth/real_ambient_pack.json
   🔐 Encrypted ambient: /Volumes/YOUR_USB_DRIVE/real_ambient_auth/encrypted_ambient_TIMESTAMP.dat
✅ Real ambient zero-knowledge pack created!

🎉 PACK READY FOR AUTHENTICATION

✅ Real ambient pack creation: SUCCESS
```

## Advanced Usage

### Custom Audio Duration
Edit `real_ambient_zero_knowledge_auth.py` line with `capture_ambient_audio(duration=60)` to change from 60 seconds.

### Custom EMF Frequency
Edit the `rtl_sdr` command frequency parameter `-f 433920000` to capture different RF bands.

### SSH Config Integration
Add to `~/.ssh/config`:
```
Host github-nfc-auth
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_real_ambient_[timestamp]
```

## System Requirements
- macOS with microphone access
- USB drive mounted at `/Volumes/YOUR_USB_DRIVE`
- NFC reader (barcode scanner compatible)
- NESDR RTL-SDR dongle (optional, has fallback)
- Python 3 with cryptography library
- ffmpeg for audio capture

---
*Zero-Knowledge NFC Authentication System - AIMF LLC*
*Generated: 2025-01-09*
