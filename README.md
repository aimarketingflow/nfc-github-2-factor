# NFC GitHub 2FA v2.0 - Interactive Installation Guide

Ultra-secure SSH authentication using physical NFC tags with interactive HTML guide and automated installer.

## 🚀 Quick Start

### Option 1: Interactive HTML Guide
```bash
open index.html  # macOS
xdg-open index.html  # Linux
```

### Option 2: Automated Installer
```bash
./install.sh
```

## 📋 Features

### v2.0 Enhancements
- **Interactive HTML Guide**: Beautiful web interface with tabs for each setup step
- **Terminal Screenshots**: Visual examples of every command and output
- **OS Detection**: Automatic platform-specific installation
- **One-Click Install**: Automated dependency installation script
- **Copy-to-Clipboard**: Easy command copying from the guide

### Core Security Features
- **Zero-Visibility Authentication**: NFC values never displayed
- **Double-Scan Verification**: Ensures accuracy without exposure
- **Physical Possession Required**: Must have the NFC tag
- **No Manual Entry**: Passphrase always captured via NFC

## 🖥️ Supported Platforms

- **Linux** (Ubuntu, Debian, Fedora)
- **macOS** (10.15+)
- **Raspberry Pi** (3/4/5 with Raspbian)

## 📦 What's Included

```
NFC_GitHub_2FA_v2/
├── index.html          # Interactive setup guide
├── install.sh          # Automated installer
├── README.md           # This file
└── scripts/            # Core authentication scripts
    ├── create_nfc_key.sh
    ├── unlock_ssh_key.sh
    ├── test_nfc_auth.sh
    └── pi_setup.sh
```

## 🔧 Manual Installation

### Prerequisites
- NFC reader (ACR122U or compatible)
- Blank NFC tags (NTAG213/215/216)
- Python 3.x
- Git

### Linux/Raspberry Pi
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip git openssh-client
sudo apt-get install libnfc-bin libnfc-dev pcscd pcsc-tools
sudo systemctl start pcscd
sudo systemctl enable pcscd
```

### macOS
```bash
brew install python3 git libnfc
# Grant Terminal.app Input Monitoring permission in System Preferences
```

## 📖 Usage

### 1. Create NFC-Protected SSH Key
```bash
./scripts/create_nfc_key.sh
```
- Scan your NFC tag twice (both scans hidden)
- Key is created with NFC ID as passphrase

### 2. Add to GitHub
1. Copy the displayed public key
2. Go to GitHub Settings → SSH and GPG keys
3. Click "New SSH key" and paste

### 3. Unlock and Use
```bash
./scripts/unlock_ssh_key.sh
# Now use git normally - key is unlocked in SSH agent
git push origin main
```

### 4. Test Authentication
```bash
./scripts/test_nfc_auth.sh
```

## 🛡️ Security Model

### Protected Against
- ✅ Remote attacks
- ✅ Keyloggers  
- ✅ Screen capture
- ✅ Credential theft
- ✅ Phishing

### Requires
- ❌ Physical NFC tag possession
- ❌ Protection against tag theft
- ❌ Backup authentication method

## ⚠️ Important Security Notes

1. **Physical Security**: Treat your NFC tag like a physical key
2. **No Recovery**: Lost tag = lost access (maintain backups)
3. **Unique Tags**: Use different tags for different services
4. **Never Record**: Don't photograph or save tag IDs

## 📱 NFC Tag Recommendations

- **NTAG213**: 180 bytes, good for single key
- **NTAG215**: 540 bytes, recommended
- **NTAG216**: 924 bytes, maximum security

## 🔍 Troubleshooting

### NFC Reader Not Detected
```bash
# Check USB connection
lsusb | grep ACR
# Restart PC/SC daemon
sudo systemctl restart pcscd
# Test with nfc-list
nfc-list
```

### Permission Denied
```bash
# Add user to dialout group (Linux)
sudo usermod -a -G dialout $USER
# Logout and login again
```

### macOS Input Issues
- System Preferences → Security & Privacy → Privacy
- Add Terminal.app to Input Monitoring

## 📚 Documentation

View the interactive guide by opening `index.html` in your browser for:
- Step-by-step installation with screenshots
- Terminal command examples
- Security best practices
- Platform-specific setup

## 📄 License

GNU General Public License v3.0 - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please ensure:
- No sensitive information in code
- Follow existing security model
- Test on multiple platforms

## 🔗 Repository

https://github.com/aimarketingflow/nfc-github-2-factor

---

**Created with 🔐 by the NFC GitHub 2FA Contributors**
