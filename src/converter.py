import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fpdf import FPDF
import html2text
import os
import re

class WebpagePDFConverter:
    def __init__(self, base_url, max_depth=2):
        self.base_url = base_url
        self.max_depth = max_depth
        self.visited_urls = set()
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.h2t = html2text.HTML2Text()
        self.configure_html2text()
        self.configure_pdf()
        
    def configure_html2text(self):
        """Configure HTML2Text settings for better content extraction"""
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_tables = False
        self.h2t.unicode_snob = True
        self.h2t.body_width = 0  # Disable text wrapping
        
    def configure_pdf(self):
        """Configure PDF settings for better formatting"""
        self.pdf.add_page()
        self.pdf.set_margin(15)  # Set margins
        self.pdf.set_font("Arial", size=11)
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same domain as base_url."""
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain

    def clean_text(self, text):
        """Clean and format text content"""
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove very long URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
        return text.strip()

    def get_page_content(self, url):
        """Fetch and parse webpage content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_links(self, html_content, current_url):
        """Extract all valid links from the page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(current_url, href)
            if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                links.add(absolute_url)
        
        return links

    def extract_main_content(self, html_content):
        """Extract the main content from the HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unnecessary elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
            
        # Try to find main content container
        main_content = soup.find('main') or soup.find(id='content') or soup.find(class_='content')
        if main_content:
            return str(main_content)
        return str(soup)

    def add_content_to_pdf(self, html_content, url):
        """Convert HTML content to text and add to PDF."""
        try:
            # Add URL as header
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 10, f"Page: {url}", ln=True)
            self.pdf.ln(5)
            
            # Extract and convert content
            main_content = self.extract_main_content(html_content)
            text_content = self.h2t.handle(main_content)
            text_content = self.clean_text(text_content)
            
            # Add content to PDF
            self.pdf.set_font("Arial", size=11)
            
            # Split content into paragraphs and add to PDF
            paragraphs = text_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    self.pdf.multi_cell(0, 6, paragraph.strip())
                    self.pdf.ln(3)
            
            self.pdf.add_page()
            
        except Exception as e:
            print(f"Error adding content from {url}: {e}")

    def crawl_and_convert(self, current_url, depth=0):
        """Recursively crawl pages and add content to PDF."""
        if depth >= self.max_depth or current_url in self.visited_urls:
            return
            
        print(f"Processing: {current_url}")
        self.visited_urls.add(current_url)
        
        html_content = self.get_page_content(current_url)
        if not html_content:
            return
            
        self.add_content_to_pdf(html_content, current_url)
        
        links = self.extract_links(html_content, current_url)
        for link in links:
            self.crawl_and_convert(link, depth + 1)

    def save_pdf(self, output_filename):
        """Save the generated PDF."""
        try:
            self.pdf.output(output_filename)
            print(f"PDF saved successfully as {output_filename}")
        except Exception as e:
            print(f"Error saving PDF: {e}")