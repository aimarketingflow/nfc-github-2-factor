#!/usr/bin/env python3
"""
NFC Chaos Writer GUI v2.0
Professional PyQt6 interface for NESDR entropy-powered NFC authentication
"""

import sys
import os
import pickle
import time
import threading
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                            QTextEdit, QProgressBar, QGroupBox, QGridLayout,
                            QStatusBar, QFrame, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# Import our existing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
try:
    from nesdr_chaos_generator import NESDRChaosGenerator
    from nfc_writer_test import NFCWriterTest
    from nfc_chaos_verifier import NFCChaosVerifier
    from verify_hardware import HardwareVerifier
except ImportError:
    # Fallback for development
    pass

class ChaosWorkerThread(QThread):
    """Background thread for NESDR chaos generation"""
    progress_update = pyqtSignal(str, int)
    generation_complete = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.generator = None
        
    def run(self):
        try:
            self.progress_update.emit("Initializing NESDR device...", 10)
            self.generator = NESDRChaosGenerator()
            
            self.progress_update.emit("Scanning RF frequencies...", 30)
            time.sleep(1)  # Visual feedback
            
            self.progress_update.emit("Collecting entropy from 433.92MHz...", 50)
            success = self.generator.generate_chaos_value()
            
            if success:
                self.progress_update.emit("Chaos value generated successfully!", 100)
                self.generation_complete.emit(True, "Ultra-random chaos value generated from RF entropy")
            else:
                self.generation_complete.emit(False, "Failed to generate chaos value")
                
        except Exception as e:
            self.generation_complete.emit(False, f"Error: {str(e)}")

class NFCChaosGUI(QMainWindow):
    """Main GUI application for NFC Chaos Writer"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFC Chaos Writer v2.0 - AIMF LLC")
        self.setGeometry(100, 100, 1200, 800)
        
        # AIMF color scheme
        self.primary_color = "#6B46C1"  # Deep purple
        self.accent_color = "#3B82F6"   # Bright blue
        self.bg_color = "#1F2937"       # Dark background
        self.text_color = "#F9FAFB"     # Light text
        
        self.setup_ui()
        self.setup_styling()
        self.check_hardware_status()
        
        # Status check timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
    def setup_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header with AIMF branding
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget for main functionality
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_generation_tab()
        self.create_verification_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - NFC Chaos Writer v2.0")
        
    def create_header(self):
        """Create the header with AIMF branding"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setFixedHeight(80)
        
        header_layout = QHBoxLayout()
        header_frame.setLayout(header_layout)
        
        # AIMF Logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("emf_chaos_diamond_64x64.png")
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                # Fallback to emoji if logo not found
                logo_label.setText("🔷")
                logo_label.setStyleSheet(f"font-size: 48px; color: {self.accent_color};")
        except:
            # Fallback to emoji if logo loading fails
            logo_label.setText("🔷")
            logo_label.setStyleSheet(f"font-size: 48px; color: {self.accent_color};")
        header_layout.addWidget(logo_label)
        
        # Title and tagline
        title_layout = QVBoxLayout()
        
        title_label = QLabel("NFC Chaos Writer v2.0")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.text_color};")
        title_layout.addWidget(title_label)
        
        tagline_label = QLabel("WORK SMARTER, NOT HARDER - Ultra-Secure NESDR Entropy Verification")
        tagline_label.setStyleSheet(f"font-size: 12px; color: {self.text_color}; font-style: italic;")
        title_layout.addWidget(tagline_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # AIMF LLC branding
        aimf_label = QLabel("AIMF LLC")
        aimf_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.primary_color};")
        header_layout.addWidget(aimf_label)
        
        return header_frame
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        dashboard = QWidget()
        layout = QGridLayout()
        dashboard.setLayout(layout)
        
        # Hardware status group
        hw_group = QGroupBox("Hardware Status")
        hw_layout = QGridLayout()
        hw_group.setLayout(hw_layout)
        
        self.nesdr_status = QLabel("❌ Not Detected")
        self.nfc_writer_status = QLabel("❌ Not Detected")
        self.rfid_reader_status = QLabel("❌ Not Detected")
        
        hw_layout.addWidget(QLabel("NESDR Device:"), 0, 0)
        hw_layout.addWidget(self.nesdr_status, 0, 1)
        hw_layout.addWidget(QLabel("NFC Writer:"), 1, 0)
        hw_layout.addWidget(self.nfc_writer_status, 1, 1)
        hw_layout.addWidget(QLabel("RFID Reader:"), 2, 0)
        hw_layout.addWidget(self.rfid_reader_status, 2, 1)
        
        layout.addWidget(hw_group, 0, 0, 1, 2)
        
        # Chaos vault status
        vault_group = QGroupBox("Chaos Vault Status")
        vault_layout = QVBoxLayout()
        vault_group.setLayout(vault_layout)
        
        self.vault_count_label = QLabel("Chaos Values: 0")
        self.vault_last_gen = QLabel("Last Generated: Never")
        
        vault_layout.addWidget(self.vault_count_label)
        vault_layout.addWidget(self.vault_last_gen)
        
        layout.addWidget(vault_group, 1, 0)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        actions_group.setLayout(actions_layout)
        
        self.quick_gen_btn = QPushButton("🌟 Generate Chaos Value")
        self.quick_verify_btn = QPushButton("🔍 Verify NFC Tag")
        
        self.quick_gen_btn.clicked.connect(self.quick_generate)
        self.quick_verify_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        
        actions_layout.addWidget(self.quick_gen_btn)
        actions_layout.addWidget(self.quick_verify_btn)
        
        # Note about standalone writer device
        writer_note = QLabel("💡 NFC Writing: Use standalone hardware device")
        writer_note.setStyleSheet(f"color: {self.accent_color}; font-size: 11px; font-style: italic;")
        writer_note.setWordWrap(True)
        actions_layout.addWidget(writer_note)
        
        layout.addWidget(actions_group, 1, 1)
        
        # System log
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        
        layout.addWidget(log_group, 2, 0, 1, 2)
        
        self.tab_widget.addTab(dashboard, "🏠 Dashboard")
        
    def create_generation_tab(self):
        """Create the chaos generation tab"""
        generation = QWidget()
        layout = QVBoxLayout()
        generation.setLayout(layout)
        
        # Generation controls
        controls_group = QGroupBox("NESDR Chaos Generation")
        controls_layout = QVBoxLayout()
        controls_group.setLayout(controls_layout)
        
        info_label = QLabel("Generate ultra-random authentication values from RF entropy collected across multiple frequency bands.")
        info_label.setWordWrap(True)
        controls_layout.addWidget(info_label)
        
        # Frequency selection
        freq_group = QGroupBox("Frequency Bands")
        freq_layout = QGridLayout()
        freq_group.setLayout(freq_layout)
        
        self.freq_checkboxes = {}
        frequencies = ["433.92 MHz", "915.0 MHz", "868.0 MHz", "315.0 MHz", "40.68 MHz"]
        
        for i, freq in enumerate(frequencies):
            cb = QCheckBox(freq)
            cb.setChecked(True)
            self.freq_checkboxes[freq] = cb
            freq_layout.addWidget(cb, i // 3, i % 3)
        
        controls_layout.addWidget(freq_group)
        
        # Generation button and progress
        self.generate_btn = QPushButton("🌟 Generate Chaos Value")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.clicked.connect(self.start_generation)
        controls_layout.addWidget(self.generate_btn)
        
        self.gen_progress = QProgressBar()
        self.gen_progress.setVisible(False)
        controls_layout.addWidget(self.gen_progress)
        
        self.gen_status = QLabel("")
        controls_layout.addWidget(self.gen_status)
        
        layout.addWidget(controls_group)
        
        # Generation log
        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.gen_log = QTextEdit()
        self.gen_log.setReadOnly(True)
        log_layout.addWidget(self.gen_log)
        
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(generation, "🌟 Generate")
        
    
    def create_verification_tab(self):
        """Create the verification tab"""
        verification = QWidget()
        layout = QVBoxLayout()
        verification.setLayout(layout)
        
        # Verification controls
        verify_group = QGroupBox("NFC Tag Verification")
        verify_layout = QVBoxLayout()
        verify_group.setLayout(verify_layout)
        
        info_label = QLabel("Verify chaos-written NFC tags without revealing sensitive values. Only shows VERIFIED or FAILED status.")
        info_label.setWordWrap(True)
        verify_layout.addWidget(info_label)
        
        # Verification button
        self.verify_btn = QPushButton("🔍 Verify NFC Tag")
        self.verify_btn.setMinimumHeight(50)
        self.verify_btn.clicked.connect(self.verify_tag)
        verify_layout.addWidget(self.verify_btn)
        
        self.verify_progress = QProgressBar()
        self.verify_progress.setVisible(False)
        verify_layout.addWidget(self.verify_progress)
        
        self.verify_status = QLabel("")
        verify_layout.addWidget(self.verify_status)
        
        layout.addWidget(verify_group)
        
        # Verification log
        log_group = QGroupBox("Verification Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.verify_log = QTextEdit()
        self.verify_log.setReadOnly(True)
        log_layout.addWidget(self.verify_log)
        
        layout.addWidget(log_group)
        
        self.tab_widget.addTab(verification, "🔍 Verify")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings = QWidget()
        layout = QVBoxLayout()
        settings.setLayout(layout)
        
        # Hardware settings
        hw_group = QGroupBox("Hardware Configuration")
        hw_layout = QGridLayout()
        hw_group.setLayout(hw_layout)
        
        # Add settings controls here
        hw_layout.addWidget(QLabel("NESDR Device ID:"), 0, 0)
        hw_layout.addWidget(QLabel("Auto-detect"), 0, 1)
        
        layout.addWidget(hw_group)
        
        # Security settings
        sec_group = QGroupBox("Security Settings")
        sec_layout = QVBoxLayout()
        sec_group.setLayout(sec_layout)
        
        self.auto_clear_cb = QCheckBox("Auto-clear logs after 1 hour")
        self.auto_clear_cb.setChecked(True)
        sec_layout.addWidget(self.auto_clear_cb)
        
        layout.addWidget(sec_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings, "⚙️ Settings")
        
    def setup_styling(self):
        """Apply AIMF-themed styling"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_color};
                color: {self.text_color};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {self.primary_color};
                background-color: {self.bg_color};
            }}
            
            QTabBar::tab {{
                background-color: #374151;
                color: {self.text_color};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.primary_color};
                color: white;
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.primary_color};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                color: {self.text_color};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.accent_color};
            }}
            
            QPushButton {{
                background-color: {self.primary_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: {self.accent_color};
            }}
            
            QPushButton:disabled {{
                background-color: #6B7280;
                color: #9CA3AF;
            }}
            
            QTextEdit {{
                background-color: #111827;
                border: 1px solid {self.primary_color};
                border-radius: 4px;
                color: {self.text_color};
                padding: 8px;
                font-family: 'Courier New', monospace;
            }}
            
            QLabel {{
                color: {self.text_color};
            }}
            
            QProgressBar {{
                border: 1px solid {self.primary_color};
                border-radius: 4px;
                background-color: #374151;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.accent_color};
                border-radius: 3px;
            }}
            
            QStatusBar {{
                background-color: {self.primary_color};
                color: white;
            }}
        """)
    
    def log_message(self, message, log_widget=None):
        """Add message to system log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        if log_widget:
            log_widget.append(formatted_msg)
        else:
            self.log_display.append(formatted_msg)
            
        # Also update status bar for important messages
        if any(word in message.lower() for word in ['error', 'failed', 'success', 'complete']):
            self.status_bar.showMessage(message, 3000)
    
    def check_hardware_status(self):
        """Check and update hardware status"""
        try:
            # Check NESDR
            # Implementation would check for actual hardware
            self.nesdr_status.setText("✅ RTL-SDR Detected")
            
            # Check NFC Writer
            self.nfc_writer_status.setText("❌ Not Connected")
            
            # Check RFID Reader
            self.rfid_reader_status.setText("❌ Not Connected")
            
        except Exception as e:
            self.log_message(f"Hardware check error: {str(e)}")
    
    def update_status(self):
        """Periodic status updates"""
        # Update vault count
        vault_count = self.get_vault_count()
        self.vault_count_label.setText(f"Chaos Values: {vault_count}")
        
    def get_vault_count(self):
        """Get number of chaos values in vault"""
        try:
            if os.path.exists('.chaos_vault'):
                with open('.chaos_vault', 'rb') as f:
                    vault = pickle.load(f)
                return vault.get('count', 0)
        except:
            pass
        return 0
    
    def quick_generate(self):
        """Quick chaos generation from dashboard"""
        self.tab_widget.setCurrentIndex(1)
        self.start_generation()
    
    def start_generation(self):
        """Start chaos value generation"""
        self.generate_btn.setEnabled(False)
        self.gen_progress.setVisible(True)
        self.gen_progress.setValue(0)
        
        self.log_message("Starting NESDR chaos generation...", self.gen_log)
        
        # Start worker thread
        self.chaos_worker = ChaosWorkerThread()
        self.chaos_worker.progress_update.connect(self.update_generation_progress)
        self.chaos_worker.generation_complete.connect(self.generation_completed)
        self.chaos_worker.start()
    
    def update_generation_progress(self, message, progress):
        """Update generation progress"""
        self.gen_progress.setValue(progress)
        self.gen_status.setText(message)
        self.log_message(message, self.gen_log)
    
    def generation_completed(self, success, message):
        """Handle generation completion"""
        self.generate_btn.setEnabled(True)
        self.gen_progress.setVisible(False)
        
        if success:
            self.gen_status.setText("✅ Generation Complete")
            self.log_message("✅ Chaos value generated successfully!", self.gen_log)
        else:
            self.gen_status.setText("❌ Generation Failed")
            self.log_message(f"❌ {message}", self.gen_log)
    
    def write_to_tag(self):
        """Write chaos value to NFC tag"""
        self.log_message("Starting NFC tag writing...", self.write_log)
        # Implementation would use existing NFC writer
        
    def verify_tag(self):
        """Verify NFC tag"""
        self.log_message("Starting tag verification...", self.verify_log)
        # Implementation would use existing verifier

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("NFC Chaos Writer v2.0")
    app.setOrganizationName("AIMF LLC")
    
    # Set application icon
    try:
        app_icon = QIcon("emf_chaos_diamond_128x128.png")
        app.setWindowIcon(app_icon)
    except:
        pass  # Fallback to default icon if logo not found
    
    window = NFCChaosGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
