import csv
import os
import re
import logging
import argparse
from meraki.sdk_client import DashboardAPI

# Setup logging
logging.basicConfig(filename='device_lookup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parse command line arguments
parser = argparse.ArgumentParser(description="Fetch device details from Meraki API including VLAN and data usage.")
parser.add_argument("-f", "--file", help="Path to file containing MAC addresses, one per line.", default="mac_addresses.txt")
parser.add_argument("-m", "--mac", help="A single MAC address to lookup.")
args = parser.parse_args()

# Configuration Variables
API_KEY = os.getenv("MERAKI_API_KEY")  # It's recommended to use an environment variable for API keys
NETWORK_ID = 'your_network_id_here'  # Replace with your actual Network ID
CSV_FILE = "device_info.csv"  # Output CSV file name

# Initialize the Meraki dashboard API
dashboard = DashboardAPI(api_key=API_KEY)

def validate_mac_address(mac):
    """Validate the MAC address format."""
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def read_mac_addresses(file_path):
    """Read and validate MAC addresses from a file, returning them as a list."""
    try:
        with open(file_path, "r") as file:
            macs = [line.strip() for line in file.readlines() if line.strip()]
            return [mac for mac in macs if validate_mac_address(mac)]
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error reading file {file_path}: {e}")
        return []

def fetch_client_details(network_id, mac_address):
    """Fetch client details by MAC address using the Meraki SDK."""
    try:
        client = dashboard.networks.get_network_client(network_id=network_id, client_id=mac_address, include_usage=True)
        return client
    except Exception as e:
        logging.error(f"Error fetching details for MAC {mac_address}: {e}")
        return None

def write_to_csv(file_path, data):
    """Write device information to a CSV file."""
    with open(file_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logging.info(f"Device information successfully written to {file_path}.")

def process_mac_addresses(network_id, mac_addresses):
    """Process a list of MAC addresses to fetch and log device details."""
    device_info_list = []
    for mac in mac_addresses:
        client_details = fetch_client_details(network_id, mac)
        if client_details:
            # Simplified data structure; extend as needed based on available client details
            device_info = {
                "MAC Address": mac,
                "Description": client_details.get("description"),
                "VLAN": client_details.get("vlan"),
                "Usage": client_details.get("usage", {}).get("total", "N/A")
            }
            device_info_list.append(device_info)
    return device_info_list

def main():
    if args.mac and validate_mac_address(args.mac):
        mac_addresses = [args.mac]
    elif args.file:
        mac_addresses = read_mac_addresses(args.file)
    else:
        logging.error("No valid input provided. Please specify a MAC address or a file with MAC addresses.")
        return

    if mac_addresses:
        device_info = process_mac_addresses(NETWORK_ID, mac_addresses)
        if device_info:
            write_to_csv(CSV_FILE, device_info)
        else:
            logging.info("No device information found for the provided MAC addresses.")
    else:
        logging.info("No valid MAC addresses to process.")

if __name__ == "__main__":
    main()
