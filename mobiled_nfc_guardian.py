#!/usr/bin/env python3
"""
Mobiled NFC Guardian - Control and monitor macOS mobiled process with NFC authentication
Prevents unauthorized mobile device attacks by gating mobiled access
"""

import subprocess
import psutil
import time
import os
import signal
import json
from datetime import datetime
import threading

class MobiledNFCGuardian:
    """Monitor and control mobiled process with NFC authentication"""
    
    def __init__(self):
        self.monitoring_active = False
        self.mobiled_enabled = False
        self.mobiled_pid = None
        self.monitor_thread = None
        self.log_file = "mobiled_guardian_log.json"
        self.auth_file = "mobiled_nfc_auth.json"
        
    def find_mobiled_process(self):
        """Find running mobiled process"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'mobiled':
                    return proc.info['pid']
        except:
            pass
        return None
    
    def kill_mobiled_process(self):
        """Safely terminate mobiled process"""
        
        mobiled_pid = self.find_mobiled_process()
        if mobiled_pid:
            try:
                print(f"🛑 Terminating mobiled process (PID: {mobiled_pid})")
                os.kill(mobiled_pid, signal.SIGTERM)
                time.sleep(2)
                
                # Force kill if still running
                if self.find_mobiled_process():
                    os.kill(mobiled_pid, signal.SIGKILL)
                    print("   Force terminated mobiled")
                
                print("✅ Mobiled process terminated")
                self.mobiled_enabled = False
                self.log_event("mobiled_terminated", {"pid": mobiled_pid, "method": "nfc_guardian"})
                return True
                
            except Exception as e:
                print(f"❌ Failed to terminate mobiled: {e}")
                return False
        else:
            print("ℹ️  Mobiled process not running")
            return True
    
    def start_mobiled_process(self):
        """Start mobiled process (it usually auto-restarts)"""
        
        try:
            print("🚀 Allowing mobiled to restart...")
            
            # Mobiled is typically managed by launchd and will restart automatically
            # We just need to ensure it's not being actively killed
            
            # Wait for it to start
            attempts = 0
            while attempts < 10:
                mobiled_pid = self.find_mobiled_process()
                if mobiled_pid:
                    print(f"✅ Mobiled restarted (PID: {mobiled_pid})")
                    self.mobiled_enabled = True
                    self.mobiled_pid = mobiled_pid
                    self.log_event("mobiled_started", {"pid": mobiled_pid, "method": "nfc_authenticated"})
                    return True
                
                time.sleep(1)
                attempts += 1
            
            print("⚠️  Mobiled did not restart automatically")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start mobiled: {e}")
            return False
    
    def authenticate_nfc_for_mobiled(self):
        """Require NFC authentication to enable mobiled"""
        
        print("\n🔐 MOBILED NFC AUTHENTICATION")
        print("=" * 40)
        print("📱 Mobiled handles iPhone/iPad connections")
        print("🛡️ NFC authentication required for security")
        
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            print("\n📟 Scan NFC tag to enable mobiled access...")
            nfc_hash = scanner.invisible_scan_simple()
            
            # Verify NFC authentication
            if self.verify_nfc_auth(nfc_hash):
                print("✅ NFC authentication successful")
                
                # Create time-limited authorization
                auth_data = {
                    'nfc_hash': nfc_hash,
                    'auth_time': time.time(),
                    'expires': time.time() + 3600,  # 1 hour expiry
                    'authorized': True
                }
                
                with open(self.auth_file, 'w') as f:
                    json.dump(auth_data, f, indent=2)
                
                print("🔓 Mobiled access authorized for 1 hour")
                return True
            else:
                print("❌ NFC authentication failed")
                return False
                
        except ImportError:
            print("⚠️  NFC scanner not available - using demo mode")
            return self.demo_auth()
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def verify_nfc_auth(self, nfc_hash):
        """Verify NFC hash against stored authorization"""
        
        # For demo, create simple verification
        # In production, this would check against secure store
        
        if not os.path.exists(self.auth_file):
            # First time - store this NFC hash
            return True
        
        try:
            with open(self.auth_file, 'r') as f:
                stored_auth = json.load(f)
            
            # Check if still authorized and not expired
            if (stored_auth.get('authorized') and 
                stored_auth.get('expires', 0) > time.time()):
                return stored_auth.get('nfc_hash') == nfc_hash
            
        except:
            pass
        
        return False
    
    def demo_auth(self):
        """Demo authentication for testing"""
        print("🎭 Demo mode - simulating NFC authentication...")
        time.sleep(2)
        print("✅ Demo authentication successful")
        return True
    
    def check_auth_status(self):
        """Check if mobiled is currently authorized"""
        
        try:
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            
            if auth_data.get('authorized') and auth_data.get('expires', 0) > time.time():
                return True
                
        except:
            pass
        
        return False
    
    def monitor_mobiled_activity(self):
        """Monitor mobiled for suspicious activity"""
        
        print("👁️  Starting mobiled monitoring...")
        
        while self.monitoring_active:
            try:
                # Check if mobiled is running when it shouldn't be
                mobiled_pid = self.find_mobiled_process()
                auth_status = self.check_auth_status()
                
                if mobiled_pid and not auth_status:
                    print(f"\n🚨 UNAUTHORIZED MOBILED DETECTED (PID: {mobiled_pid})")
                    print("   Terminating unauthorized process...")
                    self.kill_mobiled_process()
                    self.log_event("unauthorized_mobiled_killed", {"pid": mobiled_pid})
                
                elif mobiled_pid and auth_status:
                    # Monitor for suspicious activity
                    self.monitor_mobiled_connections(mobiled_pid)
                
                # Check for authorization expiry
                if auth_status:
                    with open(self.auth_file, 'r') as f:
                        auth_data = json.load(f)
                    
                    time_remaining = auth_data.get('expires', 0) - time.time()
                    if time_remaining < 300:  # 5 minutes warning
                        print(f"⏰ Mobiled authorization expires in {int(time_remaining/60)} minutes")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
    
    def monitor_mobiled_connections(self, mobiled_pid):
        """Monitor mobiled network connections for suspicious activity"""
        
        try:
            # Get network connections for mobiled process
            proc = psutil.Process(mobiled_pid)
            connections = proc.connections()
            
            suspicious_connections = []
            for conn in connections:
                # Check for suspicious remote addresses
                if conn.raddr:
                    remote_ip = conn.raddr.ip
                    
                    # Flag suspicious IPs (this is simplified)
                    if (remote_ip.startswith('10.') or 
                        remote_ip.startswith('192.168.') or
                        remote_ip.startswith('172.')):
                        # Private IPs are usually OK for local device connections
                        continue
                    else:
                        # External connections might be suspicious
                        suspicious_connections.append(conn)
            
            if suspicious_connections:
                print(f"⚠️  Suspicious mobiled connections detected: {len(suspicious_connections)}")
                self.log_event("suspicious_connections", {
                    "pid": mobiled_pid,
                    "connections": len(suspicious_connections)
                })
                
        except Exception as e:
            # Process might have terminated
            pass
    
    def log_event(self, event_type, data):
        """Log security events"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        
        # Append to log file
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            
            # Keep only last 100 events
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Logging error: {e}")
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self.monitor_mobiled_activity, daemon=True)
            self.monitor_thread.start()
            print("✅ Mobiled monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("🛑 Mobiled monitoring stopped")
    
    def get_status_report(self):
        """Get current status report"""
        
        mobiled_pid = self.find_mobiled_process()
        auth_status = self.check_auth_status()
        
        report = {
            'mobiled_running': mobiled_pid is not None,
            'mobiled_pid': mobiled_pid,
            'auth_status': auth_status,
            'monitoring_active': self.monitoring_active,
            'timestamp': datetime.now().isoformat()
        }
        
        if auth_status:
            try:
                with open(self.auth_file, 'r') as f:
                    auth_data = json.load(f)
                report['auth_expires'] = auth_data.get('expires', 0)
                report['time_remaining'] = max(0, auth_data.get('expires', 0) - time.time())
            except:
                pass
        
        return report
    
    def view_security_log(self):
        """View recent security events"""
        
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            print("\n📊 RECENT MOBILED SECURITY EVENTS")
            print("-" * 40)
            
            for event in logs[-10:]:  # Last 10 events
                timestamp = event['timestamp']
                event_type = event['event_type']
                data = event['data']
                
                print(f"⏰ {timestamp}")
                print(f"   📋 {event_type}")
                print(f"   📄 {data}")
                print()
            
            return logs
            
        except Exception as e:
            print(f"No security logs found: {e}")
            return []

def main():
    """Interactive mobiled NFC guardian"""
    
    print("🛡️ MOBILED NFC GUARDIAN")
    print("Control mobiled process with NFC authentication")
    print("Prevents unauthorized mobile device attacks")
    print()
    
    guardian = MobiledNFCGuardian()
    
    while True:
        print("\n" + "=" * 50)
        print("   MOBILED NFC GUARDIAN MENU")
        print("=" * 50)
        
        # Show current status
        status = guardian.get_status_report()
        print(f"📱 Mobiled Status: {'RUNNING' if status['mobiled_running'] else 'STOPPED'}")
        print(f"🔐 Auth Status: {'AUTHORIZED' if status['auth_status'] else 'UNAUTHORIZED'}")
        print(f"👁️  Monitoring: {'ACTIVE' if status['monitoring_active'] else 'INACTIVE'}")
        
        if status['auth_status'] and 'time_remaining' in status:
            time_remaining = int(status['time_remaining'] / 60)
            print(f"⏰ Time Remaining: {time_remaining} minutes")
        
        print("\nOptions:")
        print("1. Enable mobiled (requires NFC)")
        print("2. Disable mobiled") 
        print("3. Start monitoring")
        print("4. Stop monitoring")
        print("5. View status report")
        print("6. View security log")
        print("7. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            if guardian.authenticate_nfc_for_mobiled():
                guardian.start_mobiled_process()
                print("🎉 Mobiled enabled with NFC authentication!")
            
        elif choice == '2':
            if guardian.kill_mobiled_process():
                print("🛑 Mobiled disabled for security")
        
        elif choice == '3':
            guardian.start_monitoring()
        
        elif choice == '4':
            guardian.stop_monitoring()
        
        elif choice == '5':
            status = guardian.get_status_report()
            print("\n📊 DETAILED STATUS REPORT")
            print("-" * 30)
            for key, value in status.items():
                print(f"   {key}: {value}")
        
        elif choice == '6':
            guardian.view_security_log()
        
        elif choice == '7':
            guardian.stop_monitoring()
            print("\n👋 Mobiled NFC Guardian offline")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
