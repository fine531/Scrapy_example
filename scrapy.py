import time
import json
import random
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProductDetails:
    """Data class to store product information"""
    price: float = 0.0
    stock_status: str = "Unknown"
    rating: float = 0.0
    review_count: int = 0
    seller: str = "Unknown"
    platform: str = "Unknown"
    url: str = ""
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SeleniumScraperBase:
    """Base class for Selenium-based scrapers"""

    def __init__(self):
        self.driver = self._setup_driver

    @property
    def _setup_driver(self):
        """Setup Edge driver with appropriate options"""
        edge_options = Options()
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--disable-popup-blocking")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)

        service = Service("./msedgedriver.exe")        # Update with your path
        return webdriver.Edge(service=service, options=edge_options)

    def _wait_and_get_element(self, by, selector, timeout=10):
        """Wait for element and return it when available"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            return None

    def _safe_get_text(self, element):
        """Safely get text from element"""
        try:
            return element.text.strip() if element else ""
        except:
            return ""

class AmazonScraper(SeleniumScraperBase):
    """Scraper for Amazon products"""

    def scrape_product(self, url: str) -> ProductDetails:
        details = ProductDetails(platform="Amazon", url=url)

        try:
            self.driver.get(url)
            time.sleep(random.uniform(4, 6))

            # Price
            price_selectors = [
                "span.a-price-whole",
                "span.a-price[data-a-size=xl] ",
                "div.a-align-center, .aok-align-center"
            ]

            for selector in price_selectors:
                price_elem = self._wait_and_get_element(By.CSS_SELECTOR, selector)
                if price_elem:
                    price_text = self._safe_get_text(price_elem)
                    try:
                        details.price = float(price_text.replace('₹', '').replace(',', ''))
                        break
                    except ValueError:
                        continue

            # Stock Status
            stock_elem = self._wait_and_get_element(By.CSS_SELECTOR, "#availability")
            if stock_elem:
                details.stock_status = self._safe_get_text(stock_elem)

            # Rating
            rating_elem = self._wait_and_get_element(By.CSS_SELECTOR, "span.a-icon-alt")
            if rating_elem:
                rating_text = self._safe_get_text(rating_elem)
                try:
                    details.rating = float(rating_text.split()[0])
                except (ValueError, IndexError):
                    pass

            # Review Count
            review_elem = self._wait_and_get_element(By.CSS_SELECTOR, "#acrCustomerReviewText")
            if review_elem:
                review_text = self._safe_get_text(review_elem)
                try:
                    details.review_count = int(review_text.split()[0].replace(',', ''))
                except (ValueError, IndexError):
                    pass

            logger.info(f"Successfully scraped Amazon product: {vars(details)}")
            return details

        except Exception as e:
            logger.error(f"Error scraping Amazon product: {str(e)}")
            return details

class FlipkartScraper(SeleniumScraperBase):
    """Scraper for Flipkart products"""

    def scrape_product(self, url: str) -> ProductDetails:
        details = ProductDetails(platform="Flipkart", url=url)

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            # Price
            price_selectors = [
                "div.C7fEHH ",
                "div.UOCQB1",
                "div.hl05eU .Nx9bqj"
            ]

            for selector in price_selectors:
                price_elem = self._wait_and_get_element(By.CSS_SELECTOR, selector)
                if price_elem:
                    price_text = self._safe_get_text(price_elem)
                    try:
                        details.price = float(price_text.replace('₹', '').replace(',', ''))
                        break
                    except ValueError:
                        continue

            # Stock Status
            stock_elem = self._wait_and_get_element(By.CSS_SELECTOR, "._16FRp0")
            details.stock_status = "Out of Stock" if stock_elem else "In Stock"

            # Rating
            rating_elem = self._wait_and_get_element(By.CSS_SELECTOR, "div.XQDdHH")
            if rating_elem:
                rating_text = self._safe_get_text(rating_elem)
                try:
                    details.rating = float(rating_text)
                except ValueError:
                    pass

            # Review Count
            review_elem = self._wait_and_get_element(By.CSS_SELECTOR, "span.Y1HWO0")
            if review_elem:
                review_text = self._safe_get_text(review_elem)
                try:
                    details.review_count = int(review_text.split()[0].replace(',', ''))
                except (ValueError, IndexError):
                    pass

            logger.info(f"Successfully scraped Flipkart product: {vars(details)}")
            return details

        except Exception as e:
            logger.error(f"Error scraping Flipkart product: {str(e)}")
            return details

class ProductAnalyzer:
    """Analyzes product data from multiple sources"""

    def __init__(self):
        self.scrapers = {
            'amazon': AmazonScraper(),
            'flipkart': FlipkartScraper()
        }

    def analyze_product(self, urls: Dict[str, str]) -> Dict:
        """Analyze product across different platforms"""
        results = []

        for platform, url in urls.items():
            try:
                if platform in self.scrapers:
                    scraper = self.scrapers[platform]
                    product_details = scraper.scrape_product(url)
                    results.append(product_details)
            except Exception as e:
                logger.error(f"Error analyzing {platform}: {str(e)}")

        # Clean up Selenium drivers
        for scraper in self.scrapers.values():
            try:
                scraper.driver.quit()
            except:
                pass

        # Prepare analysis results
        analysis = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "all_results": [vars(r) for r in results],
            "error": None
        }

        # Only add comparative analysis if we have valid prices
        valid_results = [r for r in results if r.price > 0]

        if valid_results:
            best_price = min(valid_results, key=lambda x: x.price)
            highest_rated = max(valid_results, key=lambda x: x.rating)

            analysis.update({
                "best_price": {
                    "platform": best_price.platform,
                    "price": best_price.price,
                    "url": best_price.url
                },
                "highest_rated": {
                    "platform": highest_rated.platform,
                    "rating": highest_rated.rating,
                    "review_count": highest_rated.review_count,
                    "url": highest_rated.url
                },
                "average_rating": round(sum(r.rating for r in valid_results) / len(valid_results), 2)
                if any(r.rating > 0 for r in valid_results) else 0
            })
        else:
            analysis["error"] = "No valid prices found across platforms"

        return analysis

def save_analysis(analysis: Dict, filename: str = "product_analysis.json"):
    """Save analysis results to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as output_file:
            json.dump(analysis, output_file, indent=4, ensure_ascii=False)
        logger.info(f"Analysis saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")

def main():
    # Example usage
    urls = {
        "amazon": "https://www.amazon.in/Apple-iPhone-15-128GB-Black/dp/B0CHX3QBCH",
        
        "flipkart": "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    }

    analyzer = ProductAnalyzer()
    results = analyzer.analyze_product(urls)

    # Save results
    save_analysis(results)

    # Print summary
    print("\nAnalysis Summary:")
    print("-" * 50)

    if "error" in results and results["error"]:
        print(f"Error: {results['error']}")
    else:
        if "best_price" in results:
            print(f"\nBest Price:")
            print(f"Platform: {results['best_price']['platform']}")
            print(f"Price: ₹{results['best_price']['price']:,.2f}")

        if "highest_rated" in results:
            print(f"\nHighest Rated:")
            print(f"Platform: {results['highest_rated']['platform']}")
            print(f"Rating: {results['highest_rated']['rating']}/5.0")
            print(f"Review Count: {results['highest_rated']['review_count']:,}")

        if "average_rating" in results:
            print(f"\nAverage Rating Across Platforms: {results['average_rating']}/5.0")

    print("\nDetailed Results:")
    print("-" * 50)
    for result in results["all_results"]:
        print(f"\nPlatform: {result['platform']}")
        print(f"Price: ₹{result['price']:,.2f}")
        print(f"Stock Status: {result['stock_status']}")
        print(f"Rating: {result['rating']}/5.0")
        print(f"Review Count: {result['review_count']:,}")
        print(f"Seller: {result['seller']}")

if __name__ == "__main__":
    main()
