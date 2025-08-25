#!/bin/bash

# NFC GitHub 2FA v2 - Interactive Installer
# Ultra-secure SSH authentication using physical NFC tags

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            VER=$VERSION_ID
        fi
        PLATFORM="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        OS="macOS"
    elif [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        PLATFORM="raspberry"
        OS="Raspberry Pi"
    else
        PLATFORM="unknown"
        OS="Unknown"
    fi
}

# Print banner
print_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║                                                        ║"
    echo "║         🔐 NFC GitHub 2FA v2.0 Installer 🔐          ║"
    echo "║                                                        ║"
    echo "║      Ultra-Secure SSH Authentication System           ║"
    echo "║                                                        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo -e "${CYAN}Detected OS: ${GREEN}$OS${NC}"
    echo -e "${CYAN}Platform: ${GREEN}$PLATFORM${NC}"
    echo
}

# Install dependencies for Linux
install_linux_deps() {
    echo -e "${YELLOW}Installing Linux dependencies...${NC}"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then 
        APT_CMD="apt-get"
    else
        APT_CMD="sudo apt-get"
    fi
    
    $APT_CMD update
    $APT_CMD install -y python3 python3-pip git openssh-client
    $APT_CMD install -y libnfc-bin libnfc-dev pcscd pcsc-tools
    
    # Start and enable pcscd
    if command -v systemctl &> /dev/null; then
        sudo systemctl start pcscd
        sudo systemctl enable pcscd
    fi
    
    echo -e "${GREEN}✓ Linux dependencies installed${NC}"
}

# Install dependencies for macOS
install_macos_deps() {
    echo -e "${YELLOW}Installing macOS dependencies...${NC}"
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew not found. Installing...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install python3 git libnfc
    
    echo -e "${GREEN}✓ macOS dependencies installed${NC}"
    echo -e "${YELLOW}Note: Grant Terminal.app Input Monitoring permission in System Preferences${NC}"
}

# Install dependencies for Raspberry Pi
install_raspberry_deps() {
    echo -e "${YELLOW}Installing Raspberry Pi dependencies...${NC}"
    
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip git openssh-client
    sudo apt-get install -y libnfc-bin libnfc-dev pcscd pcsc-tools
    
    # Enable interfaces
    echo -e "${YELLOW}Enabling SPI and I2C interfaces...${NC}"
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_i2c 0
    
    # Start services
    sudo systemctl start pcscd
    sudo systemctl enable pcscd
    
    echo -e "${GREEN}✓ Raspberry Pi dependencies installed${NC}"
}

# Check NFC reader
check_nfc_reader() {
    echo -e "${YELLOW}Checking for NFC reader...${NC}"
    
    if command -v nfc-list &> /dev/null; then
        if nfc-list | grep -q "NFC device"; then
            echo -e "${GREEN}✓ NFC reader detected${NC}"
            nfc-list
            return 0
        else
            echo -e "${RED}⚠ No NFC reader detected${NC}"
            echo -e "${YELLOW}Please connect your NFC reader and try again${NC}"
            return 1
        fi
    else
        echo -e "${RED}NFC tools not installed properly${NC}"
        return 1
    fi
}

# Setup scripts
setup_scripts() {
    echo -e "${YELLOW}Setting up NFC authentication scripts...${NC}"
    
    # Clone repository if not already present
    if [ ! -d "scripts" ]; then
        git clone https://github.com/aimarketingflow/nfc-github-2-factor.git temp_repo
        mv temp_repo/scripts .
        rm -rf temp_repo
    fi
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    echo -e "${GREEN}✓ Scripts ready${NC}"
}

# Create systemd service (optional)
create_service() {
    echo -e "${YELLOW}Would you like to create a systemd service for automatic SSH key unlocking? (y/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cat > /tmp/nfc-ssh-unlock.service << EOF
[Unit]
Description=NFC SSH Key Unlock Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/nfc-ssh-unlock
RemainAfterExit=yes
User=$USER

[Install]
WantedBy=multi-user.target
EOF
        
        sudo mv /tmp/nfc-ssh-unlock.service /etc/systemd/system/
        sudo systemctl daemon-reload
        echo -e "${GREEN}✓ Service created (not enabled by default)${NC}"
    fi
}

# Main installation flow
main() {
    detect_os
    print_banner
    
    echo -e "${CYAN}Starting installation...${NC}"
    echo
    
    # Install dependencies based on platform
    case $PLATFORM in
        linux)
            install_linux_deps
            ;;
        macos)
            install_macos_deps
            ;;
        raspberry)
            install_raspberry_deps
            ;;
        *)
            echo -e "${RED}Unsupported platform: $PLATFORM${NC}"
            exit 1
            ;;
    esac
    
    # Check NFC reader
    if ! check_nfc_reader; then
        echo -e "${YELLOW}Please connect an NFC reader and run this installer again${NC}"
        exit 1
    fi
    
    # Setup scripts
    setup_scripts
    
    # Optional service creation (Linux only)
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "raspberry" ]]; then
        create_service
    fi
    
    echo
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Installation Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "1. Run ${YELLOW}./scripts/create_nfc_key.sh${NC} to create your NFC-protected SSH key"
    echo -e "2. Add the public key to your GitHub account"
    echo -e "3. Test with ${YELLOW}./scripts/test_nfc_auth.sh${NC}"
    echo
    echo -e "${PURPLE}For the interactive guide, open:${NC} ${YELLOW}index.html${NC}"
    echo
}

# Run main function
main
