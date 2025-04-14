import requests
from BookScraper import BookScraper 
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import urllib3

# Suppress only the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_page_links(page):
    results = []
    
    # For paginated pages:
    url = f'https://repository.kallipos.gr/simple-search?query=&filter_field_1=lang&filter_type_1=equals&filter_value_1=el&sort_by=score&order=desc&rpp=100&etal=0&start={page*100 - 100}'
    
    # Static page (for testing):
    # url = 'https://repository.kallipos.gr/handle/11419/14619'
    print(url)

    options = Options()
     
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm -usage")
    service = Service()
    

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get(url)

        columns = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'itemListValt2')))

        hrefs = []
        for column in columns:
            links = column.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href:
                    hrefs.append(href)

        

        if len(hrefs) > 100:
            print(f"Found {len(results)} links on page {page}. More than 100 links found.")
        elif len(hrefs) == 0:
            print(f"Fatal error: No links found on page {page}.")
            print('Stopping the program.')
            return False
        elif len(hrefs) < 100:
            print(f"Found {len(results)} links on page {page}. Less than 100 links found.")

        return hrefs

    except Exception as e:
        print(f"An error occurred in get_page_links (selenium) while parsing page {page}: {e}")
        return []
    finally:
        driver.quit()



def main():
    try:
        # Initialize page from file or start at 1
        try:
            with open('completed_pages.txt', 'r') as f:
                page = int(f.read().strip()) + 1  # Start from next page
        except FileNotFoundError:
            page = 1

        # Load existing data
        try:
            with open('books.json', 'r') as json_file:
                all_books_dict = json.load(json_file)
        except FileNotFoundError:
            all_books_dict = {}

        while True:
            print(f"Scraping page {page}...")
            links = get_page_links(page)
            if not links:
                print(f"No links found on page {page}. Stopping the program.")
                break
            
            for link in links:
                scraper = BookScraper(url = link)
                book_data_dict = scraper.scrape()

                all_books_dict[scraper.book_key] = book_data_dict[scraper.book_key]

            # Save progress
            with open('completed_pages.txt', 'w') as f:
                f.write(str(page))
                
            # Save data
            with open('books.json', 'w') as json_file:
                json.dump(all_books_dict, json_file, indent=4, ensure_ascii=False)
                
            print(f"Saved and Scraped {len(all_books_dict)} books so far")
            page += 1 

    except Exception as e:
        print(f"An error occurred in main.py main: {e}")



if __name__ == "__main__":
    main()
    
