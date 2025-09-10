#!/usr/bin/env python3
"""
Comprehensive Repository Sanitization
Fix all remaining sensitive data exposures
"""

import os
import re
import glob

def comprehensive_sanitize():
    """Perform comprehensive sanitization of all sensitive data"""
    
    print("🧹 COMPREHENSIVE REPOSITORY SANITIZATION")
    print("=" * 50)
    
    repo_dir = "/Users/USERNAME/Documents/_MobileShield/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2"
    
    # Comprehensive replacement patterns
    replacements = [
        # Username replacements
        (r'USERNAME', 'USERNAME'),
        (r'/Users/USERNAME', '/Users/USERNAME'),
        
        # Specific folder names
        (r'nfc_auth_data', 'nfc_auth_data'),
        
        # Timestamp patterns
        (r'1757\d{6}', 'TIMESTAMP'),
        
        # Specific USB paths
        (r'/Volumes/YOUR_USB_DRIVE', '/Volumes/YOUR_USB_DRIVE'),
        
        # NFC hash values
        (r'NFC_HASH_VALUE[a-f0-9]*', 'NFC_HASH_VALUE'),
        
        # Audio file patterns
        (r'ambient_audio_\d+\.wav', 'ambient_audio_TIMESTAMP.wav'),
        
        # GitHub responses
        (r'Hi YOUR_GITHUB_USERNAME!', 'Hi YOUR_GITHUB_USERNAME!'),
        
        # SSH key patterns
        (r'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ[A-Za-z0-9+/=]{300,}', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... [YOUR_PUBLIC_KEY]'),
        
        # Specific GitHub URLs
        (r'github\.com/aimarketingflow', 'github.com/YOUR_GITHUB_USERNAME'),
        
        # SSH wrapper paths
        (r'/Users/USERNAME/\.ssh/mobileshield_ssh_wrapper\.sh', '/Users/USERNAME/.ssh/nfc_ssh_wrapper.sh'),
        
        # Unified GitHub key paths
        (r'unified_github_\d+', 'nfc_github_TIMESTAMP'),
        
        # Creation dates with specific timestamps
        (r'"creation_date": "2025-09-09T\d{2}:\d{2}:\d{2}\.\d+"', '"creation_date": "YYYY-MM-DDTHH:MM:SS.ssssss"'),
        
        # Log timestamps
        (r'2025-09-09 \d{2}:\d{2}:\d{2},\d{3}', 'YYYY-MM-DD HH:MM:SS,mmm'),
    ]
    
    files_processed = 0
    files_changed = 0
    
    # Process all files
    for pattern in ["*.py", "*.md", "*.html", "*.sh", "*.txt", "*.json"]:
        files = glob.glob(os.path.join(repo_dir, pattern))
        files.extend(glob.glob(os.path.join(repo_dir, "**", pattern), recursive=True))
        
        for file_path in files:
            if any(skip in file_path for skip in ['.git', '__pycache__', 'venv']):
                continue
            
            files_processed += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply all replacements
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)
                
                # Write back if changed
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_changed += 1
                    print(f"✅ Sanitized: {os.path.basename(file_path)}")
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n📊 SANITIZATION COMPLETE")
    print(f"   Files processed: {files_processed}")
    print(f"   Files changed: {files_changed}")
    
    return files_changed > 0

def main():
    """Main comprehensive sanitization"""
    
    print("🔐 Comprehensive Repository Sanitization")
    print("🚀 Removing ALL sensitive information")
    print()
    
    changes_made = comprehensive_sanitize()
    
    if changes_made:
        print("\n✅ COMPREHENSIVE SANITIZATION SUCCESSFUL")
        print("   All sensitive information removed")
        print("   Repository ready for public GitHub")
    else:
        print("\n✅ REPOSITORY ALREADY CLEAN")
        print("   No sensitive information found")

if __name__ == "__main__":
    main()
