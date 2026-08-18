import re
import yaml
import getpass
from netmiko import ConnectHandler

def main():
    print("==================================================")
    print("      AUTOMATED BGP & ROUTE VALIDATION ENGINE     ")
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

    cisco_device = next(d for d in inventory if d["hostname"] == "Cisco-Core-01")
    juniper_device = next(d for d in inventory if d["hostname"] == "Juniper-Edge-01")

    # --- 1. VALIDATE JUNIPER BGP NEIGHBOR STATUS ---
    print("\n" + "=" * 55)
    print("🔍 Auditing Juniper-Edge-01 BGP Status...")
    print("=" * 55)
    
    juniper_params = {
        "device_type": juniper_device["device_type"],
        "host": juniper_device["host"],
        "port": juniper_device["port"],
        "username": username,
        "password": password,
    }

    try:
        net_connect = ConnectHandler(**juniper_params)
        bgp_out = net_connect.send_command("show bgp summary")
        net_connect.disconnect()

        if "10.255.255.1" in bgp_out and "Establ" in bgp_out:
            print("✅ JUNIPER BGP STATUS: Peer 10.255.255.1 is ESTABLISHED!")
        else:
            print("❌ JUNIPER BGP STATUS: Peer 10.255.255.1 is NOT Established.")
    except Exception as e:
        print(f"❌ Failed to validate Juniper: {e}")

    # --- 2. VALIDATE CISCO BGP NEIGHBOR & ROUTE RECEPTION ---
    print("\n" + "=" * 55)
    print("🔍 Auditing Cisco-Core-01 BGP Status & Route Table...")
    print("=" * 55)

    cisco_params = {
        "device_type": cisco_device["device_type"],
        "host": cisco_device["host"],
        "port": cisco_device["port"],
        "username": username,
        "password": password,
    }

    try:
        net_connect = ConnectHandler(**cisco_params)
        bgp_summary = net_connect.send_command("show ip bgp summary")
        route_table = net_connect.send_command("show ip route bgp")
        net_connect.disconnect()

        # Check neighbor establishment
        if "10.255.255.2" in bgp_summary and not ("Active" in bgp_summary or "Idle" in bgp_summary):
            print("✅ CISCO BGP STATUS: Peer 10.255.255.2 is ESTABLISHED!")
        else:
            print("❌ CISCO BGP STATUS: Peer 10.255.255.2 is NOT Established.")

        # Check advertised prefix
        if "172.16.100.0" in route_table:
            print("✅ ROUTE VALIDATION PASSED: 172.16.100.0/24 learned via eBGP!")
        else:
            print("❌ ROUTE VALIDATION FAILED: Prefix 172.16.100.0/24 missing from routing table.")

    except Exception as e:
        print(f"❌ Failed to validate Cisco: {e}")

    print("\n==================================================")
    print("            AUTOMATED AUDIT COMPLETE              ")
    print("==================================================")

if __name__ == "__main__":
    main()
