import requests
from urllib.parse import urljoin
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import urllib3
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_pdf(partial_pdf_url, directory, filename):
    base_url = "https://repository.kallipos.gr/"
    full_url = urljoin(base_url, partial_pdf_url)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    })

    try:
        response = session.post(full_url, verify=False, timeout=30)

        if response.status_code == 200:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True, f"{directory}_{filename}", f"Downloaded {filename} from {full_url}"

        else:
            return False, None, f"Failed to download {filename}. Status code: {response.status_code}"

    except Exception as e:
        return False, None, f"Error downloading {filename}: {e}"


def main():
    # Load JSON data from file
    with open("books.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Track progress to avoid re-downloading
    downloaded_files = set()

    # Check for already downloaded files from a progress file
    if os.path.exists("downloaded_files.txt"):
        with open("downloaded_files.txt", "r", encoding="utf-8") as progress_file:
            downloaded_files = set(progress_file.read().splitlines())

    download_tasks = []
    for item_id, item_data in data.items():
        links = item_data.get("links", {})
        for link_key, partial_url in links.items():
            safe_link_key = link_key.replace(" ", "_").replace("-", "_")
            directory = os.path.join("Data", item_id)
            filename = f"{safe_link_key}.pdf"
            if f"{directory}_{filename}" not in downloaded_files:
                download_tasks.append((partial_url, directory, filename))

    print(f"Total pending downloads: {len(download_tasks)}")

    # Download in parallel using 10 threads
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(download_pdf, partial_url, directory, filename)
            for partial_url, directory, filename in download_tasks
        ]

        for future in tqdm(as_completed(futures), total=len(download_tasks), desc="Downloading PDFs"):
            success, result, message = future.result()
            # print(message)

            if success:
                downloaded_files.add(result)
                with open("downloaded_files.txt", "a", encoding="utf-8") as progress_file:
                    progress_file.write(result + "\n")

    print("✅ All downloads finished.")


if __name__ == "__main__":
    main()
