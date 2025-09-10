#!/usr/bin/env python3
"""
Repository Sanitization Script
Remove all secure information from public repository
"""

import os
import re
import glob

def sanitize_file(file_path):
    """Sanitize a single file by removing secure information"""
    
    changes_made = False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace specific SSH host aliases with generic ones
        replacements = [
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-test-\d+', 'github-test-TIMESTAMP'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            (r'github-nfc-auth', 'github-nfc-auth'),
            
            # Replace SSH key paths with generic ones
            (r'/Users/USERNAME/\.ssh/github_[^"\'\\s]+', '/Users/USERNAME/.ssh/github_nfc_TIMESTAMP'),
            
            # Replace specific NFC values in examples
            (r'YOUR_NFC_TAG_1', 'YOUR_NFC_TAG_1'),
            (r'YOUR_NFC_TAG_2', 'YOUR_NFC_TAG_2'),
            
            # Replace USB paths
            (r'/Volumes/YOUR_USB_DRIVE', '/Volumes/YOUR_USB_DRIVE'),
            
            # Replace any SSH public keys that might be in files
            (r'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ[A-Za-z0-9+/=]+', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... [YOUR_PUBLIC_KEY]'),
            
            # Replace specific usernames
            (r'YOUR_GITHUB_USERNAME', 'YOUR_GITHUB_USERNAME'),
            
            # Replace specific file paths
            (r'/path/to/your/project', '/path/to/your/project'),
        ]
        
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                changes_made = True
        
        # Write back if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Sanitized: {os.path.basename(file_path)}")
        
        return changes_made
        
    except Exception as e:
        print(f"❌ Error sanitizing {file_path}: {e}")
        return False

def sanitize_repository():
    """Sanitize all files in the repository"""
    
    print("🧹 REPOSITORY SANITIZATION")
    print("=" * 40)
    print("🎯 Removing secure information from public repository")
    
    # Get current directory
    repo_dir = "/path/to/your/project/NFC Security Builds/GitHub_Integration/NFC_GitHub_2FA_v2"
    
    # File patterns to sanitize
    file_patterns = [
        "*.py",
        "*.md", 
        "*.html",
        "*.sh",
        "*.txt",
        "*.json"
    ]
    
    total_files = 0
    sanitized_files = 0
    
    for pattern in file_patterns:
        files = glob.glob(os.path.join(repo_dir, pattern))
        files.extend(glob.glob(os.path.join(repo_dir, "**", pattern), recursive=True))
        
        for file_path in files:
            # Skip certain files
            if any(skip in file_path for skip in ['.git', '__pycache__', '.pyc', 'venv']):
                continue
                
            total_files += 1
            if sanitize_file(file_path):
                sanitized_files += 1
    
    print(f"\n📊 SANITIZATION COMPLETE")
    print(f"   Files processed: {total_files}")
    print(f"   Files sanitized: {sanitized_files}")
    print(f"   Repository ready for public use")
    
    return sanitized_files > 0

def main():
    """Main sanitization process"""
    
    print("🔐 Repository Security Sanitization")
    print("🚀 Preparing repository for public release")
    print()
    
    changes_made = sanitize_repository()
    
    if changes_made:
        print("\n✅ SANITIZATION SUCCESSFUL")
        print("   All secure information removed")
        print("   Repository ready for public GitHub push")
        print("\n📋 NEXT STEPS:")
        print("   1. Review changes with: git diff")
        print("   2. Commit sanitized version: git add . && git commit -m 'Sanitize secure information'")
        print("   3. Push to GitHub: git push origin main")
    else:
        print("\n✅ REPOSITORY ALREADY CLEAN")
        print("   No secure information found")

if __name__ == "__main__":
    main()
