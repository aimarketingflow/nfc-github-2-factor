#!/bin/bash
# SSH NFC Wrapper - Automatically handles SSH passphrase with NFC authentication

# Set environment variables for SSH to use our NFC agent
export SSH_ASKPASS="/Users/flowgirl/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2/ssh_nfc_askpass.py"
export DISPLAY=:0  # Required for SSH_ASKPASS to work

# Activate virtual environment
cd "/Users/flowgirl/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2"
source venv_nfc_github/bin/activate

# Run SSH command with NFC authentication
ssh -o PasswordAuthentication=no -o PreferredAuthentications=publickey "$@"
