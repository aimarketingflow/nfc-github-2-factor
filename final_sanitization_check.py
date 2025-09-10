#!/usr/bin/env python3
"""
Final Repository Sanitization Check
Comprehensive audit for remaining sensitive information
"""

import os
import re
import glob

def check_for_sensitive_data():
    """Check for remaining sensitive information"""
    
    print("🔍 FINAL REPOSITORY AUDIT")
    print("=" * 40)
    
    repo_dir = "/Users/USERNAME/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2"
    
    # Patterns to look for
    sensitive_patterns = [
        (r'USERNAME', 'Username exposure'),
        (r'/Volumes/YOUR_USB_DRIVE', 'Specific USB path'),
        (r'NFC_HASH_VALUE', 'NFC hash exposure'),
        (r'nfc_auth_data', 'Specific folder name'),
        (r'1757\d{6}', 'Timestamp exposure'),
        (r'ambient_audio_\d+\.wav', 'Specific audio files'),
        (r'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ[A-Za-z0-9+/=]{300,}', 'SSH public keys'),
        (r'github\.com/aimarketingflow', 'Specific GitHub URLs'),
        (r'Hi YOUR_GITHUB_USERNAME!', 'GitHub auth responses'),
    ]
    
    issues_found = []
    
    # Check all files
    for pattern in ["*.py", "*.md", "*.html", "*.sh", "*.txt", "*.json", "*.log"]:
        files = glob.glob(os.path.join(repo_dir, pattern))
        files.extend(glob.glob(os.path.join(repo_dir, "**", pattern), recursive=True))
        
        for file_path in files:
            if any(skip in file_path for skip in ['.git', '__pycache__', 'venv']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in sensitive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        issues_found.append({
                            'file': os.path.basename(file_path),
                            'pattern': description,
                            'matches': matches[:3]  # Show first 3 matches
                        })
                        
            except Exception as e:
                print(f"⚠️  Could not read {file_path}: {e}")
    
    return issues_found

def main():
    """Main audit process"""
    
    issues = check_for_sensitive_data()
    
    if issues:
        print("❌ SENSITIVE DATA FOUND:")
        print()
        
        for issue in issues:
            print(f"📁 File: {issue['file']}")
            print(f"🔍 Issue: {issue['pattern']}")
            print(f"🎯 Matches: {issue['matches']}")
            print()
        
        print(f"📊 Total issues: {len(issues)}")
        print("🚨 REPOSITORY NOT READY FOR PUBLIC USE")
        
    else:
        print("✅ NO SENSITIVE DATA FOUND")
        print("🎉 Repository is clean and ready for public use")
        print()
        print("📋 FINAL CHECKLIST:")
        print("   ✅ No usernames exposed")
        print("   ✅ No specific USB paths")
        print("   ✅ No NFC hash values")
        print("   ✅ No SSH keys")
        print("   ✅ No specific file paths")
        print("   ✅ No log files with sensitive data")

if __name__ == "__main__":
    main()
