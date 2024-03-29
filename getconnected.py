import requests
import csv
import os
import re
import logging
import argparse

# Setup logging
logging.basicConfig(filename='device_lookup.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Fetch device details from Meraki API based on MAC address(es).')
parser.add_argument('-f', '--file', help='Path to file containing MAC addresses, one per line.', default='mac_addresses.txt')
parser.add_argument('-m', '--mac', help='A single MAC address to lookup.')
args = parser.parse_args()

# Configuration Variables
API_KEY = '123456789abcdefg'  # Replace with your actual Meraki API key
NETWORK_ID = 'your_network_id_here'  # Replace with your actual Network ID
CSV_FILE = 'device_info.csv'  # Output CSV file name

# Headers and Base URL
headers = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'}
BASE_URL = 'https://api.meraki.com/api/v1'

# Cache for storing switch details to avoid repeated API calls for the same switch
switch_cache = {}

def get_device_or_switch_details(serial):
    """Fetch device or switch details by its serial number from the cache or the API."""
    if serial in switch_cache:
        return switch_cache[serial]

    url = f"{BASE_URL}/devices/{serial}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            device_details = response.json()
            switch_cache[serial] = device_details  # Cache the result for future use
            return device_details
        else:
            logging.error(f"Error fetching details for serial {serial}: {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        logging.error(f"Network request exception for serial {serial}: {e}")
        return {}

def validate_mac_address(mac):
    """Validate the MAC address format."""
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def read_mac_addresses(file_path):
    """Read and validate MAC addresses from a file, returning them as a list."""
    try:
        with open(file_path, 'r') as file:
            macs = [line.strip() for line in file.readlines() if line.strip()]
            return [mac for mac in macs if validate_mac_address(mac)]
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error reading file {file_path}: {e}")
        return []

def write_to_csv(file_path, data):
    """Write device information to a CSV file."""
    with open(file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logging.info(f"Device information successfully written to {file_path}.")

def process_mac_addresses(mac_addresses):
    """Process a list of MAC addresses to fetch and log device details."""
    device_info_list = []
    for mac in mac_addresses:
        device_info = get_device_or_switch_details(mac)  # Adjust for correct function call
        if device_info:
            switch_details = get_device_or_switch_details(device_info.get('switchSerial', '')) if device_info.get('switchSerial') else {}
            info = {
                'MAC Address': mac,
                'Connection Type': 'Wireless' if device_info.get('ssid') else 'Wired',
                'Description': device_info.get('description', 'N/A'),
                'IP': device_info.get('ip', 'N/A'),
                'Switch Serial': device_info.get('switchSerial', 'N/A'),
                'Switch Port': device_info.get('switchPort', 'N/A'),
                'AP Name': device_info.get('ssid', 'N/A'),
                'Switch Name': switch_details.get('name', 'N/A'),
                'Switch Model': switch_details.get('model', 'N/A'),
            }
            device_info_list.append(info)
    if device_info_list:
        write_to_csv(CSV_FILE, device_info_list)

def main():
    mac_addresses = []
    if args.mac:
        if validate_mac_address(args.mac):
            mac_addresses = [args.mac]
        else:
            logging.error(f"Invalid MAC address provided: {args.mac}")
            print("Provided MAC address is invalid. Please check the format.")
            return
    else:
        if os.path.exists(args.file):
            mac_addresses = read_mac_addresses(args.file)
        else:
            logging.error(f"MAC address file not found: {args.file}")
            print(f"MAC address file not found: {args.file}.")
            return

    if mac_addresses:
        process_mac_addresses(mac_addresses)
        logging.info("Device information processing completed.")

if __name__ == "__main__":
    main()
