import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# Target channels
TARGET_CHANNELS = [
    "CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5", "CCTV-5+", 
    "CCTV-6", "CCTV-7", "CCTV-8", "CCTV-9", "CCTV-10", "CCTV-11", 
    "CCTV-12", "CCTV-13", "CCTV-14", "CCTV-15", "CCTV-16", "CCTV-17",
    "CCTV-4K"
]

def get_cctv_streams():
    print("Fetching dynamic CCTV streams from public aggregation pool...")
    url = "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.txt"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print("Failed to fetch public IP pool.")
            return {}
            
        streams = defaultdict(list)
        for line in resp.text.splitlines():
            if "," not in line:
                continue
            name, link = line.split(",", 1)
            name = name.strip().replace("高清", "").replace(" ", "")
            if name in TARGET_CHANNELS and link.startswith("http"):
                streams[name].append(link.strip())
                
        print(f"Extracted streams for {len(streams)} CCTV channels.")
        return streams
    except Exception as e:
        print(f"Error fetching IPs: {e}")
        return {}

def test_stream(link):
    start_time = time.time()
    try:
        resp = requests.get(link, stream=True, timeout=3)
        if resp.status_code == 200:
            bytes_received = 0
            for chunk in resp.iter_content(chunk_size=1024):
                bytes_received += len(chunk)
                if time.time() - start_time > 2.0:
                    break
            
            # If we received > 50KB in 2 seconds, it's valid
            if bytes_received > 50 * 1024:
                return link, bytes_received
    except Exception:
        pass
    return link, -1

def main():
    streams = get_cctv_streams()
    if not streams:
        print("No streams found. Exiting.")
        exit(1)
        
    print("Testing streams for speed and stability...")
    best_streams = defaultdict(list)
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        for channel, links in streams.items():
            # Test up to 15 links per channel to save time
            results = list(executor.map(test_stream, links[:15]))
            # Filter and sort by speed descending
            valid_results = [(link, speed) for link, speed in results if speed > 0]
            valid_results.sort(key=lambda x: x[1], reverse=True)
            
            # Keep top 3 fastest
            best_streams[channel] = [r[0] for r in valid_results[:3]]
            print(f"{channel}: Found {len(best_streams[channel])} fast streams.")
            
    print("Generating M3U file...")
    with open('cctv_live.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for channel in TARGET_CHANNELS:
            for link in best_streams.get(channel, []):
                f.write(f"#EXTINF:-1 tvg-name=\"{channel}\",{channel}\n")
                f.write(f"{link}\n")
                
    print("Successfully generated cctv_live.m3u")

if __name__ == "__main__":
    main()
