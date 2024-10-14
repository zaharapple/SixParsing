import csv
import json
import requests
import xmltodict
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from typing import List, Optional, Dict, Any


class SixStreetParsing:
    PRODUCT_PATTERN: str = '/buy-'
    SITEMAP_PATTERN: str = 'sitemap.xml'

    def __init__(self, sitemap_url: str, csv_file: str = 'products.csv') -> None:
        self.sitemap_url = sitemap_url
        self.csv_file = csv_file
        self.browser = webdriver.Chrome(options=self._get_chrome_options())

        with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['product_url', 'name', 'price', 'currency', 'brand', 'category'])

    def _get_chrome_options(self) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        return options

    def _get_product_links(self) -> List[str]:
        response = requests.get(self.sitemap_url)
        sitemap = xmltodict.parse(response.content)['urlset']['url']
        return [item['loc'] for item in sitemap if self.PRODUCT_PATTERN in item['loc']]

    def _parse_product_page(self, product_url: str) -> Optional[Dict[str, Any]]:
        self.browser.get(product_url)
        soup = BeautifulSoup(self.browser.page_source, 'lxml')

        try:
            data = soup.find("script", {"type": "application/ld+json"})
            if data:
                product_info = json.loads(data.string)
                return {
                    'product_url': product_url,
                    'name': product_info['name'],
                    'price': product_info['offers']['price'],
                    'currency': product_info['offers']['priceCurrency'],
                    'brand': product_info['brand']['name'],
                    'category': product_info.get('category', 'N/A')
                }
        except Exception as e:
            print(f"Error parsing {product_url}: {e}")
        return None

    def run(self) -> None:
        product_links = self._get_product_links()
        for product_url in product_links:
            product_data = self._parse_product_page(product_url)
            if product_data:
                self._save_to_csv(product_data)
                print(f"Saved: {product_data['name']}")

    def _save_to_csv(self, product_data: Dict[str, Any]) -> None:
        with open(self.csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                product_data['product_url'],
                product_data['name'],
                product_data['price'],
                product_data['currency'],
                product_data['brand'],
                product_data['category']
            ])

    def close(self) -> None:
        self.browser.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Web scraper.")
    parser.add_argument('url', type=str, help='URL of the sitemap')

    args = parser.parse_args()

    scraper = SixStreetParsing(args.url)
    scraper.run()
    scraper.close()
