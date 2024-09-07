#!/usr/bin/env python3

"""
Hetzner VM Snapshot Manager

This script provides a command-line interface for managing snapshots of Hetzner Cloud VMs.
It allows users to view existing snapshots and create new ones for their VMs.

Usage:
    python3 hetzner_vm_snapshot.py

Requirements:
    - Python 3.6+
    - requests library
    - rich library

Environment Variables:
    HETZNER_API_TOKEN: Your Hetzner Cloud API token (required if not using macOS Keychain)

Note: On macOS, the script can store and retrieve the API token from the Keychain for added security.
"""

import os
import sys
import json
import time
import subprocess
import argparse
import requests
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt
from rich.progress import Progress

console = Console()

def get_api_key_from_keychain() -> str:
    """
    Retrieve the Hetzner API key from macOS Keychain.

    Returns:
        str: The API key if found, otherwise an empty string.
    """
    if sys.platform != "darwin":
        print("This feature is only available on macOS.", file=sys.stderr)
        return ""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "HetznerAPIKey", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("API key not found in Keychain or access denied.", file=sys.stderr)
        return ""

# Set your Hetzner API token here
API_TOKEN = os.environ.get("HETZNER_API_TOKEN", "your_api_token_here")

# Check if we're on macOS and should use Keychain
USE_KEYCHAIN = sys.platform == "darwin"
if USE_KEYCHAIN:
    API_TOKEN = get_api_key_from_keychain() or API_TOKEN

def make_api_request(url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
    """
    Make an API request to the Hetzner Cloud API.

    Args:
        url (str): The API endpoint URL.
        method (str): The HTTP method to use (default: "GET").
        **kwargs: Additional arguments to pass to the requests.request method.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API, or None for successful DELETE requests.

    Raises:
        SystemExit: If the API request fails or returns an error.
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.request(method, url, headers=headers, **kwargs)
    
    if response.status_code == 204:  # No Content, typically for successful DELETE requests
        return None
    
    if not response.text:
        print("API Error: Empty response. Please check your API token.", file=sys.stderr)
        sys.exit(1)
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        print(f"API Error: Invalid JSON response. Status code: {response.status_code}", file=sys.stderr)
        sys.exit(1)
    
    if "error" in data:
        print(f"API Error: {data['error']['message']}", file=sys.stderr)
        sys.exit(1)
    
    return data

def get_servers() -> List[Dict[str, Any]]:
    """
    Fetch a list of all servers from the Hetzner Cloud API.

    Returns:
        List[Dict[str, Any]]: A list of server dictionaries, sorted by name.
    """
    response = make_api_request("https://api.hetzner.cloud/v1/servers")
    return sorted(response["servers"], key=lambda x: x["name"])

def get_snapshots(server_id: int, server_name: str) -> List[Dict[str, Any]]:
    """
    Fetch and filter snapshots for a specific server.

    Args:
        server_id (int): The ID of the server.
        server_name (str): The name of the server.

    Returns:
        List[Dict[str, Any]]: A list of snapshot dictionaries for the specified server.
    """
    print(f"Fetching snapshots for server ID: {server_id}")
    all_snapshots = []
    page = 1
    while True:
        response = make_api_request(f"https://api.hetzner.cloud/v1/images?type=snapshot&page={page}")
        snapshots = response.get("images", [])
        all_snapshots.extend(snapshots)
        pagination = response.get("meta", {}).get("pagination", {})
        if page >= pagination.get("last_page", page):
            break
        page += 1

    print(f"Total snapshots fetched: {len(all_snapshots)}")
    server_snapshots = []
    for snapshot in all_snapshots:
        include_reason = None
        print(f"\nProcessing snapshot {snapshot['id']}:")
        print(f"  bound_to: {snapshot.get('bound_to')}")
        print(f"  description: {snapshot.get('description')}")
        print(f"  created_from: {snapshot.get('created_from', {}).get('id')}")
        
        if snapshot.get("bound_to") == server_id:
            include_reason = "Bound to server"
            print(f"  Match: Bound to server {server_id}")
        elif snapshot.get("created_from", {}).get("id") == server_id:
            include_reason = "Created from server"
            print(f"  Match: Created from server {server_id}")
        else:
            description = snapshot.get("description", "").lower()
            server_id_str = str(server_id)
            print(f"  Checking description: '{description}'")
            print(f"  Against server ID: '{server_id_str}'")
            
            if server_id_str in description or server_name.lower() in description:
                include_reason = "Server ID or name in description"
                print("  Match: Server ID or name found in description")
        
        if include_reason:
            server_snapshots.append(snapshot)
            print(f"Including snapshot {snapshot['id']}: {include_reason}")
        else:
            print(f"Excluding snapshot {snapshot['id']}: No match")

    print(f"\nFiltered snapshots: {len(server_snapshots)}")
    return sorted(server_snapshots, key=lambda x: x["created"], reverse=True)

def display_snapshots(server_id: int, server_name: str) -> List[Dict[str, Any]]:
    """
    Display a table of snapshots for a specific server and return the list of snapshots.

    Args:
        server_id (int): The ID of the server.
        server_name (str): The name of the server.

    Returns:
        List[Dict[str, Any]]: The list of snapshots for the server.
    """
    snapshots = get_snapshots(server_id, server_name)
    console.print(Panel(f"Snapshots for VM: {server_name} (ID: {server_id})", expand=False))
    if not snapshots:
        console.print("No snapshots found for this VM.")
        console.print("You can create a new snapshot using option 1 in the menu below.")
    else:
        table = Table(title=f"Found {len(snapshots)} snapshot(s)")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        table.add_column("Bound to", style="yellow")
        table.add_column("Size (GB)", style="blue", justify="right")

        for i, snapshot in enumerate(snapshots, 1):
            created_date = snapshot['created'].split('T')[0]
            created_time = snapshot['created'].split('T')[1].split('+')[0]
            table.add_row(
                str(i),
                str(snapshot['id']),
                snapshot.get('description', 'N/A'),
                f"{created_date} at {created_time}",
                str(snapshot.get('bound_to') or 'Not bound'),
                str(snapshot.get('image_size', 'N/A'))
            )
        console.print(table)
    console.print()
    return snapshots

def create_snapshot(server_id: int) -> None:
    """
    Create a new snapshot for a specific server and wait for its completion.

    Args:
        server_id (int): The ID of the server to snapshot.
    """
    description = f"Snapshot created on {time.strftime('%Y-%m-%d %H:%M:%S')}"
    response = make_api_request(
        f"https://api.hetzner.cloud/v1/servers/{server_id}/actions/create_image",
        method="POST",
        json={"description": description}
    )
    
    action_id = response["action"]["id"]
    if not action_id:
        console.print("[bold red]Failed to get action ID. Snapshot creation may have failed.[/bold red]")
        return
    
    console.print("Waiting for snapshot to complete...")
    wait_for_snapshot_completion(action_id)

def delete_snapshot(snapshot_id: int) -> None:
    """
    Delete a snapshot.

    Args:
        snapshot_id (int): The ID of the snapshot to delete.
    """
    console.print(f"[bold yellow]Deleting snapshot with ID: {snapshot_id}[/bold yellow]")
    try:
        make_api_request(
            f"https://api.hetzner.cloud/v1/images/{snapshot_id}",
            method="DELETE"
        )
        console.print("[bold green]Snapshot deleted successfully.[/bold green]")
    except SystemExit:
        console.print("[bold red]Failed to delete snapshot.[/bold red]")

def create_snapshot(server_id: int) -> None:
    """
    Create a new snapshot for a specific server and wait for its completion.

    Args:
        server_id (int): The ID of the server to snapshot.
    """
    description = f"Snapshot created on {time.strftime('%Y-%m-%d %H:%M:%S')}"
    response = make_api_request(
        f"https://api.hetzner.cloud/v1/servers/{server_id}/actions/create_image",
        method="POST",
        json={"description": description}
    )
    
    action_id = response["action"]["id"]
    if not action_id:
        console.print("[bold red]Failed to get action ID. Snapshot creation may have failed.[/bold red]")
        return
    
    console.print("Waiting for snapshot to complete...")
    wait_for_snapshot_completion(action_id)

def wait_for_snapshot_completion(action_id: int) -> None:
    """
    Wait for a snapshot creation action to complete.

    Args:
        action_id (int): The ID of the snapshot creation action.
    """
    start_time = time.time()
    timeout = 3600  # 1 hour timeout
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Creating snapshot...", total=100)
        
        while True:
            action_status = make_api_request(f"https://api.hetzner.cloud/v1/actions/{action_id}")
            status = action_status["action"]["status"]
            current_progress = action_status["action"]["progress"]
            
            progress.update(task, completed=current_progress)
            
            if status == "success":
                progress.update(task, completed=100)
                console.print("[bold green]Snapshot created successfully![/bold green]")
                return
            elif status == "error":
                console.print("[bold red]Snapshot creation failed.[/bold red]")
                console.print("Error details:")
                console.print_json(json.dumps(action_status["action"]["error"]))
                return
            
            if time.time() - start_time > timeout:
                console.print("[bold red]Snapshot creation timed out after 1 hour.[/bold red]")
                return
            
            time.sleep(5)

def store_api_key_in_keychain(api_key: str) -> None:
    """
    Store the Hetzner API key in macOS Keychain.

    Args:
        api_key (str): The API key to store.
    """
    try:
        subprocess.run(
            ["security", "add-generic-password", "-U", "-s", "HetznerAPIKey", "-w", api_key],
            check=True
        )
        print("API key successfully stored in Keychain.")
        global API_TOKEN
        API_TOKEN = api_key
    except subprocess.CalledProcessError:
        print("Failed to store API key in Keychain.", file=sys.stderr)

def main_menu() -> None:
    """
    Display and handle the main menu of the application.
    """
    while True:
        console.print("[bold cyan]Fetching available VMs...[/bold cyan]")
        servers = get_servers()

        if not servers:
            console.print("[bold red]No VMs found. Please check your API token and try again.[/bold red]")
            return

        console.print(f"[green]Found {len(servers)} unique VMs.[/green]")

        table = Table(title="Available VMs")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("VM Name", style="magenta")

        for i, server in enumerate(servers, 1):
            table.add_row(str(i), server['name'])

        console.print(table)
        console.print("0. Store API key in Keychain (macOS only)")
        console.print("q. Quit")

        choice = Prompt.ask("Enter the number of the VM you want to manage", choices=[str(i) for i in range(len(servers) + 1)] + ['q'], show_choices=False)

        if choice.lower() == 'q':
            console.print("[yellow]Exiting script.[/yellow]")
            sys.exit(0)
        elif choice == '0':
            if USE_KEYCHAIN:
                new_api_key = Prompt.ask("Enter your Hetzner API key", password=True)
                store_api_key_in_keychain(new_api_key)
            else:
                console.print("[bold red]This feature is only available on macOS.[/bold red]")
        elif choice.isdigit() and 1 <= int(choice) <= len(servers):
            selected_server = servers[int(choice) - 1]
            manage_vm(selected_server)
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")

def manage_vm(server: Dict[str, Any]) -> None:
    """
    Display and handle the menu for managing a specific VM.

    Args:
        server (Dict[str, Any]): The server dictionary containing server details.
    """
    while True:
        console.print(f"[bold cyan]Fetching snapshots for VM: {server['name']}[/bold cyan]")
        snapshots = display_snapshots(server['id'], server['name'])
        
        console.print(Panel.fit(
            "[cyan]1.[/cyan] Create a new snapshot\n"
            "[cyan]2.[/cyan] Delete a snapshot\n"
            "[cyan]3.[/cyan] Return to main menu\n"
            "[cyan]q.[/cyan] Quit\n\n"
            "[italic]Note: Snapshots are point-in-time copies of your VM.[/italic]\n"
            "[italic]They can be used to restore your VM to a previous state or create new VMs.[/italic]",
            title="What would you like to do?",
            border_style="blue"
        ))
        
        action_choice = Prompt.ask("Enter your choice", choices=['1', '2', '3', 'q'], show_choices=False)
        
        if action_choice == '1':
            console.print(f"[bold green]Creating snapshot for VM: {server['name']}[/bold green]")
            create_snapshot(server['id'])
            Prompt.ask("Press Enter to continue")
        elif action_choice == '2':
            if snapshots:
                snapshot_choice = Prompt.ask("Enter the number of the snapshot you want to delete", choices=[str(i) for i in range(1, len(snapshots) + 1)], show_choices=False)
                snapshot_index = int(snapshot_choice) - 1
                snapshot_id = snapshots[snapshot_index]['id']
                confirm = Prompt.ask(f"Are you sure you want to delete snapshot {snapshot_id}?", choices=['y', 'n'], show_choices=False)
                if confirm.lower() == 'y':
                    delete_snapshot(snapshot_id)
            else:
                console.print("[bold yellow]No snapshots available to delete.[/bold yellow]")
            Prompt.ask("Press Enter to continue")
        elif action_choice == '3':
            break
        elif action_choice.lower() == 'q':
            console.print("[yellow]Exiting script.[/yellow]")
            sys.exit(0)
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Hetzner VM Snapshot Manager")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    if not API_TOKEN or API_TOKEN == "your_api_token_here":
        if USE_KEYCHAIN:
            print("Error: API token not found in Keychain. Please use the menu option to store it.", file=sys.stderr)
        else:
            print("Error: API token is not set. Please set the HETZNER_API_TOKEN environment variable or update the script.", file=sys.stderr)
        sys.exit(1)

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting...")
        sys.exit(1)
