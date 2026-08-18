import os
import yaml
import getpass
from datetime import datetime
from netmiko import ConnectHandler

def main():
    print("==================================================")
    print("    COMPLIANCE AUDIT & AUTOMATED BACKUP ENGINE    ")
    print("==================================================\n")

    username = input("Enter SSH Username [admin]: ") or "admin"
    password = getpass.getpass("Enter SSH Password [Password123]: ") or "Password123"

    # Load Inventory
    try:
        with open("inventory.yaml", "r") as f:
            inventory = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: 'inventory.yaml' not found.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for device_data in inventory:
        hostname = device_data["hostname"]
        device_type = device_data["device_type"]
        print("\n" + "=" * 55)
        print(f"🔍 Auditing Device: {hostname}")
        print("=" * 55)

        device_params = {
            "device_type": device_type,
            "host": device_data["host"],
            "port": device_data["port"],
            "username": username,
            "password": password,
        }

        # Select vendor-specific command to get raw running configuration
        show_config_cmd = "show running-config" if "cisco" in device_type else "show configuration"

        try:
            print(f"🔌 Connecting to {hostname}...")
            net_connect = ConnectHandler(**device_params)
            
            # Fetch Running Configuration
            print(f"📥 Retrieving active configuration ('{show_config_cmd}')...")
            running_config = net_connect.send_command(show_config_cmd)

            # Save Backup File
            backup_filename = f"backups/{hostname}_backup_{timestamp}.txt"
            with open(backup_filename, "w") as backup_file:
                backup_file.write(running_config)
            print(f"💾 Saved backup copy: '{backup_filename}'")

            # Perform Compliance Checks
            print("\n📋 Running Policy Compliance Audit:")
            print("-" * 40)

            # Compliance Policy Rules
            required_domain = device_data["vars"]["domain_name"]
            required_ntp = device_data["vars"]["ntp_server"]

            domain_check = required_domain in running_config
            ntp_check = required_ntp in running_config

            print(f"  • Domain Name ({required_domain}): {'✅ COMPLIANT' if domain_check else '❌ NON-COMPLIANT'}")
            print(f"  • NTP Server ({required_ntp}):    {'✅ COMPLIANT' if ntp_check else '❌ NON-COMPLIANT'}")

            if domain_check and ntp_check:
                print(f"\n🎉 Overall Status for {hostname}: 100% GOLD BASELINE COMPLIANT")
            else:
                print(f"\n⚠️ Overall Status for {hostname}: CONFIGURATION DRIFT DETECTED!")

            net_connect.disconnect()
            print(f"🔒 Session closed for {hostname}.\n")

        except Exception as e:
            print(f"❌ Failed to audit {hostname}: {e}\n")

if __name__ == "__main__":
    main()
    