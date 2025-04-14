from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import html
import json
import os
from bs4 import BeautifulSoup
import requests
    
class BookScraper:
    def __init__(self, url=None, driver = None,  headless=True):
        """
        Initialize the BookScraper with optional URL.
        
        Args:
            url (str, optional): URL of the book page to scrape.
            headless (bool): Run browser in headless mode if True.
        """
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize webdriver
        self.driver = driver
        
        if url:
            self.url = url
            self.book_key = "_".join(url.split('/')[-2:])
            self.book_dict = {
                self.book_key: {
                    'links': {},
                    'metadata': {}
                }
            }
        else:
            self.url = None
            self.book_key = None
            self.book_dict = {}
    
    def _initialize_driver(self):
        """Initialize the Selenium webdriver if not already initialized."""
        if self.driver is None:
            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
    
    def close(self):
        """Close the Selenium webdriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape(self, url=None):
        """
        Scrape book information from the given URL.
        
        Args:
            url (str, optional): URL to scrape. If not provided, uses the URL from initialization.
            
        Returns:
            dict: Dictionary containing book metadata and links.
        """
        try:
            if url:
                self.url = url
                self.book_key = "_".join(url.split('/')[-2:])
                self.book_dict = {
                    self.book_key: {
                        'links': {},
                        'metadata': {}
                    }
                }
                
            if not self.url:
                raise ValueError("URL is required for scraping")
            
            # # Initialize driver if not already done
            # self._initialize_driver()
            
            # # Load the page
            # self.driver.get(self.url)
            
            # # Wait for the page to load
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.CLASS_NAME, "itemMetaSection"))
            # )
            

            response = requests.get(self.url,verify=False)

            if response.status_code != 200:
                print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
                return None
            # Parse the page content with BeautifulSoup
            page_source = response.text

            # # Get page source and parse with BeautifulSoup
            # page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract download links
            self._extract_download_links(soup)
            
            # Extract metadata
            self._extract_metadata(soup)
            
            return self.book_dict
        
        except Exception as e:
            print(f"An error occurred in BookScraper.scrape: {e}")
            return None
        finally:
            # Don't close the driver here to allow for multiple scrapes
            pass
    
    def _extract_download_links(self, soup):
        """
        Extract download links from the soup object.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        """
        # Find all file rows
        file_rows = soup.find_all("div", class_="fileRow")
        
        for row in file_rows:
            # Get file type
            file_type_elem = row.find("span", class_="fileType")
            if not file_type_elem:
                continue
                
            file_type = file_type_elem.text.strip()
            
            # Find download form
            download_form = row.find("form", attrs={"method": "post"})
            if download_form:
                download_url = download_form.get("action", "")
                
                # Add to links dictionary
                if download_url:
                    self.book_dict[self.book_key]['links'][file_type] = download_url
    
    def _extract_metadata(self, soup):
        """
        Extract metadata from the soup object.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        """
        
         # Extract title specifically
        title_elem = soup.find("td", class_="metadataFieldLabel itemTitle")
        if title_elem:
            self.book_dict[self.book_key]['metadata']['Title'] = title_elem.text.strip()
        

        abstract = self._extract_abstract(soup)
        if abstract:
            self.book_dict[self.book_key]['metadata']['Abstract'] = abstract
            

        subjects = self._extract_subjects(soup)
        if subjects:
            self.book_dict[self.book_key]['metadata']['Subjects'] = subjects
        
        keywords = self._extract_keywords(soup)
        if keywords:
            self.book_dict[self.book_key]['metadata']['Keywords'] = keywords
            
        usage_stats = self._extract_usage_statistics(soup)
        if usage_stats:
            self.book_dict[self.book_key]['metadata']['Usage Statistics'] = usage_stats
        # Find all metadata rows
        metadata_rows = soup.find_all("tr")
        
        for row in metadata_rows:
            # Find label
            label_elem = row.find("td", class_="metadataFieldLabel")
            if not label_elem:
                continue
                
            label = label_elem.text.strip()
            if label.endswith(':'):
                label = label[:-1]  # Remove trailing colon
            
            # Find value
            value_elem = row.find("td", class_="metadataFieldValue")
            if not value_elem:
                continue
                
            # Extract text value
            if label == "Title" and row.find("td", class_="metadataFieldLabel itemTitle"):
                value = row.find("td", class_="metadataFieldLabel itemTitle").text.strip()
                
            elif label== 'License': 
                value = value_elem.text.strip()
                
            special_labels = ['Keywords', 'Abstract', 'Subject', 'Usage statistics']
            if any(special_label in label for special_label in special_labels):
                continue

            else:
                # Handle links in the value
                links = value_elem.find_all("a")
                if links:
                    value = []
                    for link in links:
                        link_text = link.text.strip()
                        link_url = link.get("href", "")
                        if link_text and link_url:
                            value.append({"text": link_text, "url": link_url})
                else:
                    value = value_elem.text.strip()
                    # Split by line breaks for multi-value fields
                    if "<br>" in str(value_elem) or "\n" in value:
                        value = [v.strip() for v in value.split('\n') if v.strip()]
            
            # Add to metadata dictionary
            if value:
                self.book_dict[self.book_key]['metadata'][label] = value
        
    def _extract_abstract(self, soup):
        """
        Extract abstract from the readmore div in the soup object.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        Returns:
            str: Extracted abstract text
        """
        abstract_text = ""
        
        # Find the abstract section by label
        abstract_label = soup.find("td", class_="metadataFieldLabel", string="Abstract:")
        
        if abstract_label:
            # Get the next sibling which contains the abstract value
            abstract_cell = abstract_label.find_next_sibling("td", class_="metadataFieldValue")
            
            if abstract_cell:
                # Find the readmore div that contains the abstract
                readmore_div = abstract_cell.find("div", class_="readmore")
                
                if readmore_div:
                    # First approach: Get all text content
                    full_text = readmore_div.get_text(strip=True)
                    if full_text:
                        abstract_text = full_text
                    else:
                        # Second approach: Process each element
                        paragraphs = []
                        
                        # Extract all text nodes and handle <br> tags as paragraph breaks
                        current_paragraph = ""
                        
                        for element in readmore_div.contents:
                            # If it's a string, add to current paragraph
                            if isinstance(element, str):
                                current_paragraph += element.strip() + " "
                            # If it's a <br> tag, start a new paragraph
                            elif element.name == 'br':
                                if current_paragraph.strip():
                                    paragraphs.append(current_paragraph.strip())
                                    current_paragraph = ""
                            # If it's another tag, get its text
                            elif element.name:
                                current_paragraph += element.get_text().strip() + " "
                        
                        # Add the last paragraph if not empty
                        if current_paragraph.strip():
                            paragraphs.append(current_paragraph.strip())
                        
                        # Join paragraphs with newlines
                        abstract_text = "\n".join(paragraphs)
                    
                    # If still empty, try another approach with HTML parsing
                    if not abstract_text:
                        # Get the HTML content and split by <br> tags
                        html_content = str(readmore_div)
                        # Split by <br> or <br/> or <br />
                        parts = html_content.replace('<br/>', '<br>').replace('<br />', '<br>').split('<br>')
                        
                        paragraphs = []
                        for part in parts:
                            # Create a new soup object for this part
                            part_soup = BeautifulSoup(part, 'html.parser')
                            # Get the text and strip whitespace
                            text = part_soup.get_text().strip()
                            if text and not text.startswith('<div') and not text.endswith('</div>'):
                                paragraphs.append(text)
                        
                        abstract_text = "\n".join(paragraphs)
        
        return abstract_text.strip()

    def _extract_keywords(self, soup):
        """
        Extract keywords from the readmore div in the soup object.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        Returns:
            list: List of extracted keywords
        """
        keywords = []
        
        # Find the keywords section by label
        keywords_label = soup.find("td", class_="metadataFieldLabel", string="Keywords:")
        
        if keywords_label:
            # Get the next sibling which contains the keywords value
            keywords_cell = keywords_label.find_next_sibling("td", class_="metadataFieldValue")
            
            if keywords_cell:
                # Find the readmore div that contains the keywords
                readmore_div = keywords_cell.find("div", class_="readmore")
                
                if readmore_div:
                    # Extract all text nodes directly under the readmore div
                    # This method gets all direct text children and handles the <br> tags
                    for element in readmore_div.contents:
                        # Check if it's a string and not just whitespace
                        if isinstance(element, str) and element.strip():
                            keywords.append(element.strip())
                        # If it's a tag but not a <br>, get its text
                        elif element.name and element.name != 'br' and element.string and element.string.strip():
                            keywords.append(element.string.strip())
                    
                    # If the above didn't work well, try another approach
                    if not keywords:
                        # Get the HTML content and split by <br> tags
                        html_content = str(readmore_div)
                        # Split by <br> or <br/> or <br />
                        parts = html_content.replace('<br/>', '<br>').replace('<br />', '<br>').split('<br>')
                        
                        for part in parts:
                            # Create a new soup object for this part
                            part_soup = BeautifulSoup(part, 'html.parser')
                            # Get the text and strip whitespace
                            text = part_soup.get_text().strip()
                            if text and not text.startswith('<div') and not text.endswith('</div>'):
                                keywords.append(text)
        
        # Clean up the keywords list - remove empty strings and duplicates
        keywords = [kw for kw in keywords if kw.strip()]
        keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order
        
        return keywords
        
            
            # # Extract chapters/contents
            # contents_section = soup.find("td", string="Consists of:")
            # if contents_section and contents_section.find_next_sibling("td"):
            #     contents_value = contents_section.find_next_sibling("td")
            #     chapters = []
            #     for link in contents_value.find_all("a"):
            #         chapter_text = link.text.strip()
            #         chapter_url = link.get("href", "")
            #         if chapter_text and chapter_url:
            #             chapters.append({"title": chapter_text, "url": chapter_url})
                
            #     if chapters:
            #         self.book_dict[self.book_key]['metadata']['Chapters'] = chapters
        
    def _extract_subjects(self, soup):
        """
        Extract subject categories from the soup object.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        Returns:
            list: Hierarchical subject categories
        """
        subjects = []
        results = []
        # Find the subject section by label
        subject_label = soup.find("td", class_="metadataFieldLabel", string="Subject:")
        
        if subject_label:
            # Get the next sibling which contains the subject values
            subject_cell = subject_label.find_next_sibling("td", class_="metadataFieldValue")
            
            if subject_cell:
                # Find all the subject links
                subject_links = subject_cell.find_all("a")
                
                for link in subject_links:
                    # Get the text and clean it up
                    subject_text = link.get_text().strip()
                    
                    # Replace ">" with :: for hierarchical structure
                    subject_text = subject_text.replace(" > ", "::")
                    
                    # Split the text by :: to get the hierarchical levels
                    subject_hierarchy = subject_text.split("::")
                    
                    # Clean up each level
                    subject_hierarchy = [level.strip() for level in subject_hierarchy]
                    
                    # Store as a structured object
                    if subject_hierarchy:
                        # subjects.append({
                        #     "full_path": subject_text,
                        #     "hierarchy": subject_hierarchy,
                        #     "leaf": subject_hierarchy[-1] if subject_hierarchy else ""
                        # })
                        results.append(subject_hierarchy[-1] if subject_hierarchy else "")
                    else :
                        results.append('')
        
            return results
    

            def scrape_multiple(self, urls):
                """
                Scrape multiple book pages.
                
                Args:
                    urls (list): List of URLs to scrape.
                    
                Returns:
                    dict: Dictionary containing all scraped book information.
                """
                results = {}
                
                try:
                    # Initialize driver if not already done
                    self._initialize_driver()
                    
                    for url in urls:
                        print(f"Scraping {url}")
                        book_data = self.scrape(url)
                        if book_data:
                            results.update(book_data)
                        time.sleep(1)  # Be nice to the server
                    
                    return results
                
                except Exception as e:
                    print(f"An error occurred in BookScraper.scrape_multiple: {e}")
                    return results
                finally:
                    self.close()
    
    def _extract_usage_statistics(self, soup):
        """
        Extract usage statistics from the analytics section.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page.
        Returns:
            dict: Dictionary with usage statistics
        """
        stats = {}
        
        # Find the analytics row
        analytics_row = soup.find("tr", class_="analyticsTr")
        
        if analytics_row:
            # Find the analytics value cell
            analytics_cell = analytics_row.find("td", class_="metadataFieldValue")
            
            if analytics_cell:
                # Find the bookAnalytics div
                analytics_div = analytics_cell.find("div", class_="bookAnalytics")
                
                if analytics_div:
                    # Find all the individual statistic divs
                    stat_divs = analytics_div.find_all("div")
                    
                    for div in stat_divs:
                        # Get the text and split by colon
                        stat_text = div.get_text().strip()
                        if ":" in stat_text:
                            key, value = stat_text.split(":", 1)
                            stats[key.strip()] = value.strip()
        
        return stats