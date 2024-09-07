# Hetzner VM Snapshot Manager

## Overview

The Hetzner VM Snapshot Manager is a Python-based command-line tool designed to simplify the management of snapshots for Hetzner Cloud virtual machines (VMs). This tool provides an intuitive interface for viewing, creating, and deleting snapshots of your Hetzner Cloud VMs.

## Features

- List all available Hetzner Cloud VMs
- Display existing snapshots for a selected VM
- Create new snapshots with progress tracking
- Delete existing snapshots
- Secure API key storage using macOS Keychain (for macOS users)

## Requirements

- Python 3.6 or higher
- `requests` library
- `rich` library
- Hetzner Cloud API token

## Installation

1. Clone this repository or download the `hetzner_vm_snapshot.py` file.

2. Install the required Python libraries:

   ```
   pip3 install requests rich
   ```

3. Ensure you have a Hetzner Cloud API token. You can generate one in the Hetzner Cloud Console under "Access" > "API Tokens".

## Usage

Run the script using Python 3:

```
python3 hetzner_vm_snapshot.py
```

### API Token Configuration

You have two options for configuring your API token:

1. **Environment Variable**: Set the `HETZNER_API_TOKEN` environment variable with your API token.

2. **macOS Keychain**: On macOS, you can securely store your API token in the Keychain. Use option 0 in the main menu to store your API token.

### Main Menu

The main menu displays all available VMs and provides the following options:

- Select a VM to manage its snapshots
- Store API key in Keychain (macOS only)
- Quit the application

### VM Management Menu

After selecting a VM, you can:

1. Create a new snapshot
2. Delete an existing snapshot
3. Return to the main menu

## Testing

To run the unit tests, use the following command:

```
python3 -m unittest test_hetzner_vm_snapshot.py
```

## Contributing

Contributions to the Hetzner VM Snapshot Manager are welcome! Please feel free to submit pull requests, create issues, or suggest new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Disclaimer

This tool is not officially associated with Hetzner. Use it at your own risk and ensure you comply with Hetzner's terms of service and API usage guidelines.
