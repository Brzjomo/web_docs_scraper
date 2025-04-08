import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import html2text
import re
import sys
import subprocess
import winreg
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin

class MayaDocsScraper:
    def __init__(self):
        # Load configuration
        self.config = self.load_config()
        self.base_url = self.config.get("base_url", "")
        self.url_keyword = self.config["url_keyword"]
        self.output_dir = self.config.get("output_dir", "")
        
        # Setup HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0
        
        # Create output directory if it doesn't exist
        if not self.output_dir:
            # Extract domain from first URL in sitemap
            domain = self.get_domain_from_sitemap()
            if domain:
                self.output_dir = domain
            else:
                self.output_dir = "scraped_docs"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")  # Suppress most console output
        
        try:
            if sys.platform == "win32":
                # Check if Chrome is installed
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                
                chrome_installed = False
                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_installed = True
                        chrome_path = path
                        print(f"Found Chrome at: {path}")
                        break
                
                if not chrome_installed:
                    raise Exception("Google Chrome not found. Please install Chrome first.")
                
                # Get Chrome version from registry
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                    version, _ = winreg.QueryValueEx(key, "version")
                    print(f"Chrome version: {version}")
                except Exception as e:
                    print(f"Could not determine Chrome version from registry: {str(e)}")
                    try:
                        # Fallback to command line
                        version = subprocess.check_output(
                            f'"{chrome_path}" --version',
                            shell=True,
                            stderr=subprocess.STDOUT
                        ).decode('gbk').strip()  # Use gbk encoding for Chinese Windows
                        print(f"Chrome version (from command): {version}")
                    except Exception as e:
                        print(f"Could not determine Chrome version: {str(e)}")
                
                # Use chromedriver.exe from project directory
                chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
                if not os.path.exists(chromedriver_path):
                    raise Exception(f"chromedriver.exe not found in project directory: {chromedriver_path}")
                
                print(f"Using chromedriver from: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # For other platforms
                self.driver = webdriver.Chrome(options=chrome_options)
                
        except Exception as e:
            print("\nError initializing Chrome WebDriver. Please check the following:")
            print("1. Google Chrome is installed on your system")
            print("2. Your Chrome version matches the WebDriver version")
            print("3. You have the necessary permissions to run Chrome")
            print("\nTroubleshooting steps:")
            print("1. Make sure Chrome is installed in the default location")
            print("2. Make sure chromedriver.exe exists in the project directory")
            print("3. Run the script without 'sudo' (Windows doesn't use sudo)")
            print("4. Try running the script from an administrator command prompt")
            print("5. If problems persist, try reinstalling Chrome")
            print(f"\nError details: {str(e)}")
            sys.exit(1)
    
    def get_domain_from_sitemap(self):
        """Extract domain from first URL in sitemap"""
        try:
            sitemap_path = os.path.join(os.getcwd(), "sitemap.xml")
            if not os.path.exists(sitemap_path):
                return None
            
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            # Define the namespace
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Get first URL
            first_url = root.find('.//ns:url/ns:loc', ns)
            if first_url is not None:
                parsed_url = urlparse(first_url.text)
                return parsed_url.netloc
            
            return None
            
        except Exception as e:
            print(f"Error extracting domain from sitemap: {str(e)}")
            return None
    
    def load_config(self):
        """Load configuration from JSON file"""
        config_path = os.path.join(os.getcwd(), "scraper_config.json")
        if not os.path.exists(config_path):
            print("Configuration file not found. Creating default configuration...")
            default_config = {
                "base_url": "",
                "url_keyword": "",
                "output_dir": "",
                "max_retries": 3,
                "initial_delay": 5,
                "second_pass_retries": 5,
                "second_pass_delay": 10
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            sys.exit(1)
    
    def get_links_from_sitemap(self):
        """Get links from sitemap.xml file"""
        try:
            sitemap_path = os.path.join(os.getcwd(), "sitemap.xml")
            if not os.path.exists(sitemap_path):
                raise Exception(f"sitemap.xml not found in project directory: {sitemap_path}")
            
            print("Reading sitemap.xml...")
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            # Define the namespace
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Find all URLs in the sitemap
            urls = []
            for url in root.findall('.//ns:url', ns):
                loc = url.find('ns:loc', ns)
                if loc is not None:
                    # If url_keyword is empty, collect all URLs
                    if not self.url_keyword or self.url_keyword in loc.text:
                        urls.append(loc.text)
            
            if self.url_keyword:
                print(f"Found {len(urls)} URLs containing '{self.url_keyword}' in sitemap.xml")
            else:
                print(f"Found {len(urls)} URLs in sitemap.xml (no keyword filter)")
            return urls
            
        except Exception as e:
            print(f"Error reading sitemap.xml: {str(e)}")
            return []
    
    def get_filename_from_url(self, url):
        """Generate filename from URL"""
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Get the path and remove leading/trailing slashes
        path = parsed_url.path.strip('/')
        
        # Replace slashes with underscores
        path = path.replace('/', '_')
        
        # Remove any invalid characters
        path = re.sub(r'[^\w\-_\. ]', '_', path)
        
        # Add .md extension if not present
        if not path.endswith('.md'):
            path += '.md'
            
        return path
    
    def load_progress(self):
        """Load progress from previous run"""
        progress_file = os.path.join(self.output_dir, "progress.json")
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading progress file: {str(e)}")
        return {"completed_urls": [], "current_index": 0, "failed_urls": []}
    
    def save_progress(self, completed_urls, current_index, failed_urls):
        """Save progress to file"""
        progress_file = os.path.join(self.output_dir, "progress.json")
        try:
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({
                    "completed_urls": completed_urls,
                    "current_index": current_index,
                    "failed_urls": failed_urls
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving progress file: {str(e)}")
    
    def convert_relative_urls(self, html_content, base_url):
        """Convert relative URLs to absolute URLs in HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Convert links
        for a in soup.find_all('a', href=True):
            a['href'] = urljoin(base_url, a['href'])
        
        # Convert images
        for img in soup.find_all('img', src=True):
            img['src'] = urljoin(base_url, img['src'])
        
        # Convert scripts
        for script in soup.find_all('script', src=True):
            script['src'] = urljoin(base_url, script['src'])
        
        # Convert stylesheets
        for link in soup.find_all('link', href=True):
            link['href'] = urljoin(base_url, link['href'])
        
        return str(soup)
    
    def scrape_page_with_retry(self, url, max_retries=None, initial_delay=None):
        """Scrape a page with retry mechanism and exponential backoff"""
        if max_retries is None:
            max_retries = self.config["max_retries"]
        if initial_delay is None:
            initial_delay = self.config["initial_delay"]
            
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                print(f"Scraping page: {url} (Attempt {attempt + 1}/{max_retries})")
                self.driver.get(url)
                time.sleep(delay)  # Wait for page to load with exponential backoff
                
                # Get the page content
                content = self.driver.find_element(By.TAG_NAME, "body").get_attribute("outerHTML")
                
                # Convert to markdown
                markdown = self.h2t.handle(content)
                
                # Add original URL at the end
                markdown += f"\n\n---\n\nOriginal URL: {url}"
                
                # Create filename from URL
                filename = self.get_filename_from_url(url)
                
                # Create directory structure based on URL path
                filepath = os.path.join(self.output_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save to file
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown)
                    
                print(f"Saved: {filename}")
                return True
                
            except (WebDriverException, TimeoutException) as e:
                print(f"Error scraping {url} (Attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    delay *= 2  # Exponential backoff
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Failed to scrape {url} after {max_retries} attempts")
                    return False
            except Exception as e:
                print(f"Unexpected error scraping {url}: {str(e)}")
                return False
    
    def retry_failed_urls(self, failed_urls):
        """Retry failed URLs with increased retry count and delay"""
        print(f"\nStarting second pass for {len(failed_urls)} failed URLs...")
        success_count = 0
        
        for url in failed_urls:
            print(f"\nRetrying failed URL: {url}")
            if self.scrape_page_with_retry(
                url,
                max_retries=self.config["second_pass_retries"],
                initial_delay=self.config["second_pass_delay"]
            ):
                success_count += 1
                failed_urls.remove(url)
        
        print(f"\nSecond pass completed. Successfully retried {success_count} URLs.")
        return failed_urls
    
    def run(self):
        """Main execution method"""
        print("Starting Maya documentation scraping...")
        links = self.get_links_from_sitemap()
        print(f"Found {len(links)} pages to scrape")
        
        # Load progress
        progress = self.load_progress()
        completed_urls = set(progress["completed_urls"])
        start_index = progress["current_index"]
        failed_urls = set(progress["failed_urls"])
        
        # Check if all URLs have been processed
        if len(completed_urls) + len(failed_urls) == len(links):
            print("\nAll URLs have been processed. Only retrying failed URLs...")
            if failed_urls:
                remaining_failed_urls = self.retry_failed_urls(list(failed_urls))
                if remaining_failed_urls:
                    print(f"\nWarning: {len(remaining_failed_urls)} URLs still failed after all retries:")
                    for url in remaining_failed_urls:
                        print(f"- {url}")
                self.save_progress(list(completed_urls), len(links), list(remaining_failed_urls))
            else:
                print("No failed URLs to retry.")
            self.driver.quit()
            return
        
        print(f"Resuming from index {start_index} with {len(completed_urls)} completed URLs")
        
        # First pass: scrape all URLs
        for i, url in enumerate(links[start_index:], start_index):
            if url in completed_urls:
                print(f"Skipping already completed URL: {url}")
                continue
                
            print(f"Scraping page {i + 1}/{len(links)}: {url}")
            if self.scrape_page_with_retry(url):
                completed_urls.add(url)
                if url in failed_urls:
                    failed_urls.remove(url)
            else:
                failed_urls.add(url)
            
            # Save progress after each URL
            self.save_progress(list(completed_urls), i + 1, list(failed_urls))
        
        # Second pass: retry failed URLs
        if failed_urls:
            remaining_failed_urls = self.retry_failed_urls(list(failed_urls))
            if remaining_failed_urls:
                print(f"\nWarning: {len(remaining_failed_urls)} URLs still failed after all retries:")
                for url in remaining_failed_urls:
                    print(f"- {url}")
        
        self.driver.quit()
        print("\nScraping completed!")
        print(f"Successfully scraped: {len(completed_urls)} URLs")
        print(f"Failed to scrape: {len(failed_urls)} URLs")

if __name__ == "__main__":
    scraper = MayaDocsScraper()
    scraper.run() 