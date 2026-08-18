import yaml
import getpass
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

def main():
    print("==================================================")
    print("      NETWORK AUTOMATION ENGINE — DEPLOYMENT     ")
    print("==================================================\n")

    # 1. Prompt for SSH Credentials
    username = input("Enter SSH Username [admin]: ") or "admin"
    password = getpass.getpass("Enter SSH Password [Password123]: ") or "Password123"

    # 2. Set up Jinja2 Template Environment
    env = Environment(loader=FileSystemLoader("templates"))

    # 3. Load Inventory YAML File
    try:
        with open("inventory.yaml", "r") as f:
            inventory = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: 'inventory.yaml' not found in current directory.")
        return

    # 4. Process Each Device in the Inventory
    for device_data in inventory:
        hostname = device_data["hostname"]
        print("\n" + "=" * 55)
        print(f"🚀 Processing Device: {hostname}")
        print("=" * 55)

        # Render Jinja2 Template with Device Variables
        template_name = device_data["template"]
        template = env.get_template(template_name)
        config_payload = template.render(device_data["vars"])

        print(f"\n📝 Rendered Jinja2 Configuration Payload:")
        print("-" * 45)
        print(config_payload)
        print("-" * 45)

        # Prepare Netmiko Connection Parameters
        device_params = {
            "device_type": device_data["device_type"],
            "host": device_data["host"],
            "port": device_data["port"],
            "username": username,
            "password": password,
        }

        # Connect and Push Configuration via Netmiko
        try:
            print(f"\n🔌 Connecting to {hostname} ({device_data['host']})...")
            net_connect = ConnectHandler(**device_params)
            print("✅ SSH Session Established!")

            print("⚙️ Pushing configuration commands...")
            config_lines = [
                line.strip() 
                for line in config_payload.splitlines() 
                if line.strip() and not line.strip().startswith("!")
            ]
            
            output = net_connect.send_config_set(config_lines)
            print("\n📄 Device CLI Response:")
            print(output)

            # --- JUNOS COMMIT FIX ---
            if "juniper" in device_data["device_type"]:
                print("\n💾 Committing Junos configuration...")
                commit_output = net_connect.commit()
                print(commit_output)

            # Verification Check
            verify_cmd = device_data.get("verify_cmd")
            verify_match = device_data.get("verify_match")
            if verify_cmd:
                print(f"\n🔍 Executing Automated Verification: '{verify_cmd}'...")
                verify_output = net_connect.send_command(verify_cmd)
                
                if verify_match in verify_output:
                    print(f"✅ VERIFICATION PASSED: Found expected value '{verify_match}' on {hostname}!")
                else:
                    print(f"⚠️ VERIFICATION FAILED: Could not find '{verify_match}' in output.")

            net_connect.disconnect()
            print(f"🔒 Disconnected safely from {hostname}.\n")

        except Exception as e:
            print(f"❌ Connection or Execution Failed for {hostname}: {e}\n")

if __name__ == "__main__":
    main()
EOF