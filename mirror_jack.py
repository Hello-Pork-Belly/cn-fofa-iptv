import requests
import re
import os

URL = "https://php.946985.filegear-sg.me/jackTV.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def mirror_and_optimize():
    print(f"Fetching {URL}...")
    headers = {"User-Agent": USER_AGENT}
    
    try:
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
        content = resp.text
        
        # Inject standard User-Agent for all streams to prevent future blocking by the author
        # This adds VLC/Kodi compatible UA tags before the stream URLs
        lines = content.splitlines()
        optimized_lines = []
        for line in lines:
            if line.startswith("http://") or line.startswith("https://"):
                # Add UA camouflage tag before the URL
                optimized_lines.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
            optimized_lines.append(line)
            
        final_m3u = "\r\n".join(optimized_lines)
        
        with open("jack_mirror.m3u", "w", encoding="utf-8") as f:
            f.write(final_m3u)
            
        print("Successfully mirrored and optimized jackTV.m3u")
    except Exception as e:
        print(f"Failed to fetch or process M3U: {e}")
        exit(1)

if __name__ == "__main__":
    mirror_and_optimize()
