import os
import json
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# Channels configuration
with open('channels.json', 'r', encoding='utf-8') as f:
    CHANNELS = json.load(f)

def get_public_ips():
    print("Fetching dynamic UDPXY IPs from public aggregation pool (Bypassing FOFA)...")
    url = "https://raw.githubusercontent.com/Guovin/TV/gd/result.txt"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print("Failed to fetch public IP pool.")
            return []
        
        # Extract all unique IP:PORT combinations from the m3u/txt file
        ip_pattern = re.compile(r"http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})")
        ips = list(set(ip_pattern.findall(resp.text)))
        print(f"Extracted {len(ips)} potential UDPXY IPs from public pool.")
        return ips
    except Exception as e:
        print(f"Error fetching IPs: {e}")
        return []

def test_ip(ip):
    # Test our specific Sichuan Telecom multicast address to verify if the IP belongs to Sichuan Telecom
    test_url = f"http://{ip}/udp/239.93.0.58:5140"
    start_time = time.time()
    try:
        resp = requests.get(test_url, stream=True, timeout=3)
        if resp.status_code == 200:
            bytes_received = 0
            for chunk in resp.iter_content(chunk_size=1024):
                bytes_received += len(chunk)
                if time.time() - start_time > 2.0:
                    break
            
            # If we received > 50KB in 2 seconds, it's a valid Sichuan Telecom IP!
            if bytes_received > 50 * 1024:
                print(f"[OK] Sichuan Telecom IP Found: {ip} (Speed: {bytes_received/1024:.2f} KB/2s)")
                return ip
    except Exception:
        pass
    return None

def main():
    ips = get_public_ips()
    if not ips:
        print("No IPs found. Exiting.")
        exit(1)
        
    print("Testing IPs for Sichuan Telecom multicast access and stability...")
    valid_ips = []
    # Test concurrently to find matching IPs fast
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(test_ip, ips)
        for res in results:
            if res:
                valid_ips.append(res)
                if len(valid_ips) >= 3:
                    break
                    
    if not valid_ips:
        print("No stable Sichuan Telecom IPs found in today's pool.")
        exit(1)
        
    print(f"Selected Top IPs: {valid_ips}")
    
    print("Generating M3U file...")
    with open('cctv_live.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for channel_name, multicast_addr in CHANNELS.items():
            for ip in valid_ips:
                f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\",{channel_name}\n")
                f.write(f"http://{ip}/udp/{multicast_addr}\n")
                
    print("Successfully generated cctv_live.m3u")

if __name__ == "__main__":
    main()
