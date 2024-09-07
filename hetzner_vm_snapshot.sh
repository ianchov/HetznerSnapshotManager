#!/bin/bash

echo "This script has been replaced by a Python version."
echo "Please use 'hetzner_vm_snapshot.py' instead."
echo "Run it with: python3 hetzner_vm_snapshot.py"

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Your current Python version is: $python_version"
echo "This script requires Python 3.6 or higher."

# Check for required libraries
echo "Checking for required libraries..."
python3 -c "import requests" 2>/dev/null || echo "Warning: 'requests' library is not installed. Please install it using: pip3 install requests"
python3 -c "import rich" 2>/dev/null || echo "Warning: 'rich' library is not installed. Please install it using: pip3 install rich"

echo "For more information, please refer to the script's documentation."
