import os
import json
import base64
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# FOFA configuration
FOFA_EMAIL = os.environ.get("FOFA_EMAIL")
FOFA_KEY = os.environ.get("FOFA_KEY")
SEARCH_QUERY = 'app="udpxy" && subdivisions="Sichuan" && isp="China Telecom"'

# Target channels
with open('channels.json', 'r', encoding='utf-8') as f:
    CHANNELS = json.load(f)

def get_fofa_ips():
    print(f"Searching FOFA for: {SEARCH_QUERY}")
    qbase64 = base64.b64encode(SEARCH_QUERY.encode('utf-8')).decode('utf-8')
    url = f"https://fofa.info/api/v1/search/all?email={FOFA_EMAIL}&key={FOFA_KEY}&qbase64={qbase64}&size=20"
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("error"):
            print(f"FOFA API Error: {data.get('errmsg')}")
            return []
            
        results = data.get("results", [])
        ips = [f"{r[0]}:{r[1]}" for r in results]
        print(f"FOFA found {len(ips)} IPs.")
        return ips
    except Exception as e:
        print(f"Failed to query FOFA: {e}")
        return []

def test_ip(ip):
    # Test CCTV-1 multicast address to verify Sichuan Telecom intranet access
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
            
            # If we received > 50KB in 2 seconds, it's valid
            if bytes_received > 50 * 1024:
                print(f"[OK] {ip} (Speed: {bytes_received/1024:.2f} KB/2s)")
                return ip
    except Exception:
        pass
    return None

def main():
    if not FOFA_EMAIL or not FOFA_KEY:
        print("Error: FOFA credentials not set.")
        exit(1)
        
    ips = get_fofa_ips()
    if not ips:
        print("No IPs found. Exiting.")
        exit(1)
        
    print("Testing IPs for stability...")
    valid_ips = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_ip, ips)
        for res in results:
            if res:
                valid_ips.append(res)
                if len(valid_ips) >= 3:
                    break
                    
    if not valid_ips:
        print("No stable IPs found.")
        exit(1)
        
    print(f"Selected Top IPs: {valid_ips}")
    
    print("Generating M3U file...")
    with open('cctv_live.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for channel, addr in CHANNELS.items():
            for ip in valid_ips:
                f.write(f"#EXTINF:-1 tvg-name=\"{channel}\",{channel}\n")
                f.write(f"http://{ip}/udp/{addr}\n")
                
    print("Successfully generated cctv_live.m3u")

if __name__ == "__main__":
    main()
