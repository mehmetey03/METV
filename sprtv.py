import requests
import os
import re
import tempfile
import shutil
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def update_playlist():
    # Get M3U URL from environment variable
    m3u_url = os.getenv('TV_M3U_SOURCE_URL')
    if not m3u_url:
        raise ValueError("TV_M3U_SOURCE_URL environment variable not set")
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    try:
        # Fetch the M3U content with timeout
        response = http.get(
            m3u_url,
            timeout=30,  # 30 seconds timeout
            headers={'User-Agent': 'M3U-Playlist-Updater/1.0'}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Use the content as-is since it already includes the EPG URL and header
        m3u_content = response.text
        
        # Write to the repository root
        output_filename = "tv.m3u"
        # Use the current working directory (repository root)
        output_path = os.path.join(os.getcwd(), output_filename)
        print(f"Writing to: {output_path}")
        
        # Write directly to the output file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            
            # Verify the file was written
            if not os.path.exists(output_path):
                raise Exception(f"Failed to create {output_filename}")
                
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception(f"Created empty file {output_filename}")
                
            print(f"Successfully updated {output_filename}")
            print(f"File size: {file_size} bytes")
            
        except Exception as e:
            print(f"Error writing to {output_path}: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise
            
        return True  # Success
        
    except Exception as e:
        print(f"Error updating M3U playlist: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_playlist()
