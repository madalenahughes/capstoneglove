import os
import requests

def download_database():
    url = "DIRECT_DOWNLOAD_LINK_HERE"
    output_path = "database.db"

    # Make sure to download the database only if it doesn't already exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(output_path):
        print(f"Downloading database from {url}...")
        response = requests.get(url, stream=True)
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print("Download complete.")
    else:
        print("Database already exists. Skipping download.")

if __name__ == "__main__":
    download_database()