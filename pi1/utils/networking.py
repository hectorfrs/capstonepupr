import os
import time

def setup_network(network_config):
    ethernet_ip = network_config['ethernet']['ip']
    wifi_ssid = network_config['wifi']['ssid']
    wifi_password = network_config['wifi']['password']
    wifi_ip = network_config['wifi']['ip']

    print(f"Trying to configure network with Ethernet (IP: {ethernet_ip})...")
    eth_status = os.system(f"sudo ifconfig eth0 {ethernet_ip} netmask 255.255.255.0")
    
    if eth_status == 0:  # 0 indica éxito
        os.system(f"sudo route add default gw {network_config['ethernet']['gateway']}")
        print("Ethernet network setup complete.")
    else:
        print("Ethernet setup failed. Trying Wi-Fi...")
        os.system(f"sudo ifconfig wlan0 down")
        time.sleep(2)
        os.system(f"sudo ifconfig wlan0 up")
        wifi_status = os.system(f"sudo iwconfig wlan0 essid {wifi_ssid} key s:{wifi_password}")
        
        if wifi_status == 0:  # 0 indica éxito
            print("Wi-Fi connected.")
            os.system(f"sudo ifconfig wlan0 {wifi_ip} netmask 255.255.255.0")
            os.system(f"sudo route add default gw {network_config['wifi']['gateway']}")
            print("Wi-Fi network setup complete.")
        else:
            print("Wi-Fi setup failed. No network connection available.")
