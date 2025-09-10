#!/usr/bin/env python3
"""
Create Test SSH Key with Known Passphrase
Generate SSH key with simple passphrase for testing auto-injection
"""

import subprocess
import os
import sys
from datetime import datetime

def create_ssh_key_with_passphrase(passphrase="1234"):
    """Create SSH key with known passphrase"""
    
    print("🔑 CREATING TEST SSH KEY WITH KNOWN PASSPHRASE")
    print("=" * 50)
    
    # Generate timestamp for unique key name
    timestamp = int(datetime.now().timestamp())
    key_name = f"github_test_{timestamp}"
    key_path = os.path.expanduser(f"~/.ssh/{key_name}")
    
    print(f"🔐 Passphrase: {'*' * len(passphrase)} (hidden)")
    print(f"📁 Key path: {key_path}")
    
    try:
        # Generate SSH key with known passphrase
        cmd = [
            'ssh-keygen',
            '-t', 'rsa',
            '-b', '2048',
            '-f', key_path,
            '-N', passphrase,  # Set passphrase
            '-C', f'test-key-{timestamp}@github.com'
        ]
        
        print("🔨 Generating SSH key...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ SSH key generation failed: {result.stderr}")
            return None
        
        print("✅ SSH key generated successfully")
        
        # Set proper permissions
        os.chmod(key_path, 0o600)
        os.chmod(f"{key_path}.pub", 0o644)
        
        print("✅ Permissions set correctly")
        
        # Read public key
        with open(f"{key_path}.pub", 'r') as f:
            public_key = f.read().strip()
        
        print(f"\n📋 PUBLIC KEY:")
        print(public_key)
        
        # Update SSH config
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        host_alias = f"github-test-{timestamp}"
        
        config_entry = f"""
# Test SSH key with known passphrase
Host {host_alias}
    HostName github.com
    User git
    IdentityFile {key_path}
"""
        
        with open(ssh_config_path, 'a') as f:
            f.write(config_entry)
        
        print(f"\n✅ SSH config updated with host: {host_alias}")
        
        return {
            'key_path': key_path,
            'public_key': public_key,
            'host_alias': host_alias,
            'passphrase': passphrase
        }
        
    except Exception as e:
        print(f"❌ Error creating SSH key: {e}")
        return None

def test_auto_passphrase_with_new_key(key_info):
    """Test auto-passphrase injection with the new key"""
    
    print(f"\n🧪 TESTING AUTO-PASSPHRASE WITH NEW KEY")
    print("=" * 50)
    
    import tempfile
    
    # Create temporary askpass script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(f'#!/bin/bash\necho "{key_info["passphrase"]}"\n')
        temp_askpass = f.name
    
    os.chmod(temp_askpass, 0o700)
    
    try:
        # Set environment for SSH_ASKPASS
        env = os.environ.copy()
        env['SSH_ASKPASS'] = temp_askpass
        env['DISPLAY'] = ':0'
        env['SSH_ASKPASS_REQUIRE'] = 'force'
        
        print(f"🔑 Testing SSH with host: {key_info['host_alias']}")
        print("🔒 Passphrase will be injected automatically...")
        
        # Test SSH connection
        result = subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            '-T', key_info['host_alias']
        ], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        
        print(f"📤 SSH Exit Code: {result.returncode}")
        
        if result.stdout:
            print("📋 SSH Output:")
            print(result.stdout)
        
        if result.stderr:
            print("📋 SSH Messages:")
            print(result.stderr)
        
        # Clean up
        os.unlink(temp_askpass)
        
        # Check if authentication worked
        success = result.returncode == 1 and "successfully authenticated" in result.stderr
        
        if success:
            print("\n🎉 AUTO-PASSPHRASE TEST SUCCESSFUL")
            print("   ✅ Passphrase injected automatically")
            print("   ✅ SSH key authenticated with GitHub")
        else:
            print("\n⚠️  SSH connection completed (add public key to GitHub to test authentication)")
        
        return success
        
    except Exception as e:
        if os.path.exists(temp_askpass):
            os.unlink(temp_askpass)
        print(f"❌ SSH test error: {e}")
        return False

def main():
    """Main test SSH key creation"""
    
    print("🔑 Test SSH Key Generator with Known Passphrase")
    print("🚀 Creates SSH key with simple passphrase for auto-injection testing")
    print()
    
    # Create SSH key with known passphrase
    key_info = create_ssh_key_with_passphrase("1234")
    
    if not key_info:
        print("❌ Failed to create SSH key")
        return
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. Copy the public key above to GitHub Settings > SSH and GPG keys")
    print(f"2. Test auto-passphrase injection:")
    print(f"   ssh -T {key_info['host_alias']}")
    print(f"3. Or run the auto-test below...")
    
    # Ask if user wants to test immediately
    test_now = input("\nTest auto-passphrase injection now? (y/n): ").strip().lower()
    
    if test_now == 'y':
        test_auto_passphrase_with_new_key(key_info)
    
    print(f"\n🔐 KEY SUMMARY:")
    print(f"   Host alias: {key_info['host_alias']}")
    print(f"   Key path: {key_info['key_path']}")
    print(f"   Passphrase: {'*' * len(key_info['passphrase'])}")

if __name__ == "__main__":
    main()
