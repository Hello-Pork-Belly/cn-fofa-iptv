import os
import requests

TARGET_CHANNELS = {
    "CCTV1": "CCTV-1", "CCTV2": "CCTV-2", "CCTV3": "CCTV-3", 
    "CCTV4": "CCTV-4", "CCTV5": "CCTV-5", "CCTV5+": "CCTV-5+", 
    "CCTV6": "CCTV-6", "CCTV7": "CCTV-7", "CCTV8": "CCTV-8", 
    "CCTV9": "CCTV-9", "CCTV10": "CCTV-10", "CCTV11": "CCTV-11", 
    "CCTV12": "CCTV-12", "CCTV13": "CCTV-13", "CCTV14": "CCTV-14", 
    "CCTV15": "CCTV-15", "CCTV16": "CCTV-16", "CCTV17": "CCTV-17",
    "CCTV4K": "CCTV-4K"
}

def main():
    print("Fetching pre-verified CCTV streams from public aggregation pool...")
    url = "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.txt"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print("Failed to fetch public IP pool.")
            exit(1)
            
        streams = {v: [] for v in TARGET_CHANNELS.values()}
        
        for line in resp.text.splitlines():
            if "," not in line:
                continue
            name, link = line.split(",", 1)
            name = name.strip().replace("高清", "").replace(" ", "")
            link = link.split("$")[0].strip()  # Remove tags like $LR...
            
            # Match channel and prefer IPv4 (GitHub Actions overseas might fail on IPv6)
            if name in TARGET_CHANNELS and link.startswith("http://") and "[" not in link:
                std_name = TARGET_CHANNELS[name]
                if len(streams[std_name]) < 3:
                    streams[std_name].append(link)
                    
        print("Generating M3U file...")
        with open('cctv_live.m3u', 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for channel, links in streams.items():
                for link in links:
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel}\",{channel}\n")
                    f.write(f"{link}\n")
                    
        print("Successfully generated cctv_live.m3u")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
