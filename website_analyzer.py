from crewai import Agent, Task, Crew, Process
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Dict, List
import json
import logging
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class WebsiteAnalyzer:
    def __init__(self, url: str, use_ai: bool = False):
        self.url = self._normalize_url(url)
        self.soup = None
        self.page_content = None
        self.driver = None
        self.use_ai = use_ai
        self.load_page_content()
        if self.page_content:
            logger.info(f"Fetched HTML content length: {len(self.page_content)} bytes")
            if len(self.page_content) < 1000:
                logger.warning("Fetched HTML content is very short. The site may be blocking bots or is mostly dynamic.")
        else:
            logger.warning("No HTML content fetched.")

    def _normalize_url(self, url: str) -> str:
        """Normalize the URL to ensure it has the correct format"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def _setup_selenium(self):
        """Set up Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Updated headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Add platform-specific options
            if platform.system() == 'Windows':
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-software-rasterizer')
                chrome_options.add_argument('--remote-debugging-port=9222')
            
            # Try to use the Chrome path from environment variable
            chrome_path = os.getenv('CHROME_PATH')
            if chrome_path and os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
            
            # Use the latest ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # Add error handling for WebDriver creation
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                logger.error(f"Failed to create Chrome WebDriver: {str(e)}")
                # Try alternative approach
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-popup-blocking')
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
        except Exception as e:
            logger.error(f"Failed to set up Selenium: {str(e)}")
            self.driver = None

    def load_page_content(self):
        """Load and parse the webpage content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            self.page_content = response.text
            self.soup = BeautifulSoup(self.page_content, 'html.parser')
            
            # Set up Selenium for dynamic content
            self._setup_selenium()
            if self.driver:
                self.driver.get(self.url)
                time.sleep(2)  # Wait for dynamic content to load
                self.page_content = self.driver.page_source
                self.soup = BeautifulSoup(self.page_content, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error loading page: {str(e)}")
            self.page_content = None
            self.soup = None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.page_content = None
            self.soup = None

    def __del__(self):
        """Cleanup Selenium WebDriver"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def create_ux_agent(self) -> Agent:
        """Create the UX analysis agent"""
        if not self.use_ai:
            return None
            
        return Agent(
            role='UX Analyst',
            goal='Analyze website user experience and provide improvement suggestions',
            backstory="""You are an expert UX analyst with years of experience in 
            evaluating website usability and user experience. You specialize in 
            identifying navigation issues, readability problems, and layout inconsistencies.""",
            verbose=True,
            allow_delegation=False
        )

    def create_seo_agent(self) -> Agent:
        """Create the SEO analysis agent"""
        if not self.use_ai:
            return None
            
        return Agent(
            role='SEO Specialist',
            goal='Analyze website SEO elements and provide optimization suggestions',
            backstory="""You are a seasoned SEO specialist who excels at identifying 
            technical SEO issues and providing actionable recommendations for 
            improving search engine visibility.""",
            verbose=True,
            allow_delegation=False
        )

    def create_performance_agent(self) -> Agent:
        """Create the performance analysis agent"""
        if not self.use_ai:
            return None
            
        return Agent(
            role='Performance Engineer',
            goal='Analyze website performance and provide optimization suggestions',
            backstory="""You are a performance optimization expert who specializes in 
            identifying and resolving website speed and optimization issues.""",
            verbose=True,
            allow_delegation=False
        )

    def analyze_ux(self) -> Dict:
        """Analyze UX aspects of the website"""
        if not self.soup:
            return {"error": "Failed to load page content", "score": 0}

        try:
            nav = self._check_navigation()
            read = self._check_readability()
            layout = self._check_layout()
            access = self._check_accessibility()
            # Score: count how many checks are 'good' (e.g., not empty, not all False)
            score = 0
            total = 4
            if nav and isinstance(nav, dict) and not nav.get('error'):
                score += 1
            if read and isinstance(read, dict) and not read.get('error'):
                score += 1
            if layout and isinstance(layout, dict) and not layout.get('error'):
                score += 1
            if access and isinstance(access, dict) and not access.get('error'):
                score += 1
            percent = int((score / total) * 100)
            return {
                "navigation": nav,
                "readability": read,
                "layout": layout,
                "accessibility": access,
                "score": percent
            }
        except Exception as e:
            logger.error(f"Error in UX analysis: {str(e)}")
            return {"error": f"UX analysis failed: {str(e)}", "score": 0}

    def _check_navigation(self) -> Dict:
        """Check navigation elements"""
        try:
            nav_links = self.soup.find_all('a')
            broken_links = []
            for link in nav_links:
                href = link.get('href')
                if href and not href.startswith(('http', '#', 'mailto:', 'tel:')):
                    try:
                        full_url = self._normalize_url(href)
                        response = requests.head(full_url, timeout=5)
                        if response.status_code >= 400:
                            broken_links.append(href)
                    except:
                        broken_links.append(href)

            return {
                "total_links": len(nav_links),
                "broken_links": broken_links,
                "suggestions": [
                    "Ensure all navigation links are working",
                    "Implement clear navigation hierarchy",
                    "Add breadcrumbs for better user orientation",
                    "Include a sitemap for better navigation"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking navigation: {str(e)}")
            return {"error": f"Navigation check failed: {str(e)}"}

    def _check_readability(self) -> Dict:
        """Check readability aspects"""
        try:
            text_elements = self.soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            paragraphs = self.soup.find_all('p')
            avg_paragraph_length = sum(len(p.get_text().split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0

            return {
                "total_text_elements": len(text_elements),
                "average_paragraph_length": round(avg_paragraph_length, 2),
                "suggestions": [
                    "Use clear and concise headings",
                    "Maintain consistent font sizes",
                    "Ensure sufficient contrast between text and background",
                    "Keep paragraphs short and focused"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking readability: {str(e)}")
            return {"error": f"Readability check failed: {str(e)}"}

    def _check_layout(self) -> Dict:
        """Check layout consistency"""
        try:
            # Check for common layout elements
            has_header = bool(self.soup.find(['header', 'nav']))
            has_footer = bool(self.soup.find('footer'))
            has_main = bool(self.soup.find('main'))
            
            return {
                "has_header": has_header,
                "has_footer": has_footer,
                "has_main": has_main,
                "suggestions": [
                    "Maintain consistent spacing between elements",
                    "Ensure responsive design for all screen sizes",
                    "Use a grid system for better alignment",
                    "Implement proper semantic HTML structure"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking layout: {str(e)}")
            return {"error": f"Layout check failed: {str(e)}"}

    def _check_accessibility(self) -> Dict:
        """Check basic accessibility features"""
        try:
            has_aria_labels = bool(self.soup.find(attrs={"aria-label": True}))
            has_alt_text = bool(self.soup.find('img', alt=True))
            has_skip_links = bool(self.soup.find('a', attrs={"href": "#main-content"}))
            
            return {
                "has_aria_labels": has_aria_labels,
                "has_alt_text": has_alt_text,
                "has_skip_links": has_skip_links,
                "suggestions": [
                    "Add ARIA labels to interactive elements",
                    "Ensure all images have descriptive alt text",
                    "Implement skip navigation links",
                    "Use semantic HTML elements"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking accessibility: {str(e)}")
            return {"error": f"Accessibility check failed: {str(e)}"}

    def analyze_seo(self) -> Dict:
        """Analyze SEO aspects of the website"""
        if not self.soup:
            return {"error": "Failed to load page content", "score": 0}

        try:
            meta = self._check_meta_tags()
            alt = self._check_alt_tags()
            headings = self._check_headings()
            mobile = self._check_mobile_friendliness()
            content = self._analyze_content()
            # Score: count how many checks are 'good' (e.g., not empty, not all False)
            score = 0
            total = 5
            if meta and isinstance(meta, dict) and not meta.get('error'):
                score += 1
            if alt and isinstance(alt, dict) and not alt.get('error'):
                score += 1
            if headings and isinstance(headings, dict) and not headings.get('error'):
                score += 1
            if mobile and isinstance(mobile, dict) and not mobile.get('error'):
                score += 1
            if content and isinstance(content, dict) and not content.get('error'):
                score += 1
            percent = int((score / total) * 100)
            return {
                "meta_tags": meta,
                "alt_tags": alt,
                "headings": headings,
                "mobile_friendliness": mobile,
                "content_analysis": content,
                "score": percent
            }
        except Exception as e:
            logger.error(f"Error in SEO analysis: {str(e)}")
            return {"error": f"SEO analysis failed: {str(e)}", "score": 0}

    def _check_meta_tags(self) -> Dict:
        """Check meta tags"""
        try:
            meta_tags = self.soup.find_all('meta')
            title = self.soup.find('title')
            description = self.soup.find('meta', attrs={'name': 'description'})
            keywords = self.soup.find('meta', attrs={'name': 'keywords'})
            
            return {
                "has_title": bool(title),
                "has_description": bool(description),
                "has_keywords": bool(keywords),
                "total_meta_tags": len(meta_tags),
                "suggestions": [
                    "Ensure unique and descriptive title tag",
                    "Add meta description",
                    "Include relevant meta keywords",
                    "Add Open Graph and Twitter card meta tags"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking meta tags: {str(e)}")
            return {"error": f"Meta tags check failed: {str(e)}"}

    def _check_alt_tags(self) -> Dict:
        """Check image alt tags"""
        try:
            images = self.soup.find_all('img')
            images_without_alt = [img for img in images if not img.get('alt')]
            images_with_empty_alt = [img for img in images if img.get('alt') == '']
            
            return {
                "total_images": len(images),
                "images_without_alt": len(images_without_alt),
                "images_with_empty_alt": len(images_with_empty_alt),
                "suggestions": [
                    "Add descriptive alt text to all images",
                    "Use relevant keywords in alt text",
                    "Keep alt text concise and meaningful",
                    "Avoid using generic alt text like 'image' or 'photo'"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking alt tags: {str(e)}")
            return {"error": f"Alt tags check failed: {str(e)}"}

    def _check_headings(self) -> Dict:
        """Check heading structure"""
        try:
            headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            h1_count = len(self.soup.find_all('h1'))
            heading_hierarchy = {f'h{i}': len(self.soup.find_all(f'h{i}')) for i in range(1, 7)}
            
            return {
                "total_headings": len(headings),
                "h1_count": h1_count,
                "heading_hierarchy": heading_hierarchy,
                "suggestions": [
                    "Use only one H1 tag per page",
                    "Maintain proper heading hierarchy",
                    "Include relevant keywords in headings",
                    "Ensure headings are descriptive and meaningful"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking headings: {str(e)}")
            return {"error": f"Headings check failed: {str(e)}"}

    def _check_mobile_friendliness(self) -> Dict:
        """Check mobile friendliness"""
        try:
            viewport = self.soup.find('meta', attrs={'name': 'viewport'})
            media_queries = self.soup.find_all('link', attrs={'media': True})
            touch_elements = self.soup.find_all(['button', 'a', 'input'])
            
            return {
                "has_viewport": bool(viewport),
                "has_media_queries": len(media_queries) > 0,
                "touch_elements": len(touch_elements),
                "suggestions": [
                    "Implement responsive design",
                    "Optimize touch targets for mobile",
                    "Ensure readable font sizes on mobile",
                    "Test website on various mobile devices"
                ]
            }
        except Exception as e:
            logger.error(f"Error checking mobile friendliness: {str(e)}")
            return {"error": f"Mobile friendliness check failed: {str(e)}"}

    def _analyze_content(self) -> Dict:
        """Analyze content quality and structure"""
        try:
            paragraphs = self.soup.find_all('p')
            total_words = sum(len(p.get_text().split()) for p in paragraphs)
            images = self.soup.find_all('img')
            
            return {
                "total_words": total_words,
                "total_images": len(images),
                "content_ratio": len(images) / total_words if total_words > 0 else 0,
                "suggestions": [
                    "Ensure content is unique and valuable",
                    "Maintain a good balance of text and images",
                    "Use internal linking to related content",
                    "Include calls-to-action where appropriate"
                ]
            }
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            return {"error": f"Content analysis failed: {str(e)}"}

    def analyze_performance(self) -> Dict:
        """Analyze website performance"""
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=10)
            load_time = time.time() - start_time
            headers = response.headers
            has_compression = 'gzip' in headers.get('content-encoding', '').lower()
            has_cache_control = 'cache-control' in headers
            has_keep_alive = headers.get('connection', '').lower() == 'keep-alive'
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = len(soup.find_all('script'))
            styles = len(soup.find_all('link', rel='stylesheet'))
            images = len(soup.find_all('img'))
            page_size = len(response.content) / 1024  # KB
            # Score: basic heuristic
            score = 0
            total = 4
            if load_time < 3:
                score += 1
            if has_compression:
                score += 1
            if has_cache_control:
                score += 1
            if page_size < 2048:  # <2MB
                score += 1
            percent = int((score / total) * 100)
            return {
                "load_time": f"{load_time:.2f}s",
                "page_size": f"{page_size:.2f}KB",
                "resource_count": {
                    "scripts": scripts,
                    "stylesheets": styles,
                    "images": images
                },
                "optimization_features": {
                    "compression_enabled": has_compression,
                    "caching_enabled": has_cache_control,
                    "keep_alive_enabled": has_keep_alive
                },
                "score": percent,
                "suggestions": [
                    "Optimize image sizes and formats",
                    "Implement browser caching",
                    "Minify CSS, JavaScript, and HTML",
                    "Use a CDN for static assets",
                    "Enable compression",
                    "Consider lazy loading for images"
                ]
            }
        except Exception as e:
            logger.error(f"Error in performance analysis: {str(e)}")
            return {
                "error": f"Performance analysis failed: {str(e)}",
                "score": 0,
                "suggestions": [
                    "Check if the website is accessible",
                    "Verify network connectivity",
                    "Ensure the URL is correct"
                ]
            }

    def run_analysis(self) -> Dict:
        """Run the complete website analysis"""
        try:
            # Get the analysis results
            ux_analysis = self.analyze_ux()
            seo_analysis = self.analyze_seo()
            performance_analysis = self.analyze_performance()
            # Fallback if all scores are 0
            if (ux_analysis.get('score', 0) == 0 and
                seo_analysis.get('score', 0) == 0 and
                performance_analysis.get('score', 0) == 0):
                fallback_msg = "Unable to analyze this site. It may use JavaScript-heavy content or block bots."
                ux_analysis['error'] = fallback_msg
                seo_analysis['error'] = fallback_msg
                performance_analysis['error'] = fallback_msg
            return {
                "url": self.url,
                "ux_analysis": ux_analysis,
                "seo_analysis": seo_analysis,
                "performance_analysis": performance_analysis
            }
        except Exception as e:
            logger.error(f"Error running analysis: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "url": self.url
            }

def main():
    # Example usage
    url = "https://example.com"  # Replace with the website you want to analyze
    use_ai = bool(os.getenv('OPENAI_API_KEY'))  # Only use AI if API key is available
    
    print(f"Running analysis with AI features {'enabled' if use_ai else 'disabled'}")
    analyzer = WebsiteAnalyzer(url, use_ai=use_ai)
    results = analyzer.run_analysis()
    
    # Print results in a formatted way
    print("\nWebsite Analysis Results:")
    print("=" * 50)
    print(f"URL: {results['url']}")
    
    if "error" in results:
        print(f"\nError: {results['error']}")
        return
    
    print("\nUX Analysis:")
    print("-" * 20)
    print(json.dumps(results['ux_analysis'], indent=2))
    
    print("\nSEO Analysis:")
    print("-" * 20)
    print(json.dumps(results['seo_analysis'], indent=2))
    
    print("\nPerformance Analysis:")
    print("-" * 20)
    print(json.dumps(results['performance_analysis'], indent=2))

if __name__ == "__main__":
    main() 