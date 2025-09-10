#!/usr/bin/env python3
"""
Test NFC Authentication - Interactive Demo
Shows exactly how to provide NFC input for GitHub authentication
"""

import subprocess
import sys
import os

def test_github_nfc_auth():
    """Test GitHub NFC authentication with manual input guide"""
    
    print("🔐 GITHUB NFC AUTHENTICATION TEST")
    print("=" * 50)
    print()
    print("📋 INSTRUCTIONS:")
    print("1. The script will ask for FIRST NFC scan (unlock ambient data)")
    print("   → Type: 1249919116 and press Enter")
    print()
    print("2. The script will ask for SECOND NFC scan (passphrase assembly)")  
    print("   → Type: 99999999999 and press Enter")
    print()
    print("3. The system will then attempt SSH connection to GitHub")
    print()
    
    input("Press Enter to start the authentication test...")
    print()
    
    # Change to the correct directory and run the script
    os.chdir('/Users/flowgirl/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2')
    
    # Activate venv and run
    cmd = "source venv_nfc_github/bin/activate && python3 github_nfc_connect.py"
    
    print("🚀 Starting GitHub NFC authentication...")
    print("   Follow the prompts and enter the NFC values as instructed above")
    print()
    
    # Run the command in interactive mode
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    test_github_nfc_auth()
