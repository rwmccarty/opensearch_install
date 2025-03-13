#!/bin/bash

# Configuration file path
CONFIG_FILE="install_rpms.config"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found"
    exit 1
fi

# Source the entire config file to get all variables
source "$CONFIG_FILE"

# Verify DOWNLOADS_DIR was set in config
if [ -z "$DOWNLOADS_DIR" ]; then
    echo "Error: DOWNLOADS_DIR not set in configuration file"
    exit 1
fi



# Check if downloads directory exists
if [ ! -d "$DOWNLOADS_DIR" ]; then
    echo "Error: Downloads directory $DOWNLOADS_DIR not found"
    exit 1
fi

# Find all rpm variables and build the RPMS array
RPMS=()
for var in $(compgen -v | grep '^rpm'); do
    value="${!var}"
    if [[ "$value" =~ \.rpm$ ]]; then
        RPMS+=("$DOWNLOADS_DIR/$value")
    fi
done

# Check if we found any RPMs
if [ ${#RPMS[@]} -eq 0 ]; then
    echo "Error: No RPMs found in configuration file"
    exit 1
fi

# Function to install an RPM
install_rpm() {
    local rpm_file=$1
    echo "Installing $rpm_file..."
    
    if [ ! -f "$rpm_file" ]; then
        echo "Error: $rpm_file not found"
        return 1
    fi
    
    # Install the RPM with yum
    sudo yum localinstall "$rpm_file" -y --verbose --nogpgcheck
    
    if [ $? -eq 0 ]; then
        echo "Successfully installed $rpm_file"
        return 0
    else
        echo "Failed to install $rpm_file"
        return 1
    fi
}

# Print RPMs to be installed
echo "Found ${#RPMS[@]} RPMs to install from $DOWNLOADS_DIR:"
printf '%s\n' "${RPMS[@]}"
echo "-----------------------------------"

# Main installation loop
for rpm in "${RPMS[@]}"; do
    install_rpm "$rpm"
    if [ $? -ne 0 ]; then
        echo "Installation failed for $rpm"
        exit 1
    fi
done

echo "All RPMs installed successfully"
