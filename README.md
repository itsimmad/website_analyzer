# Website Analyzer

A Python project that uses CrewAI to analyze websites for UX, SEO, and performance improvements. The analyzer uses multiple specialized agents to provide comprehensive website analysis and suggestions for improvement.

## Features

- **UX Analysis**
  - Navigation structure analysis
  - Readability assessment
  - Layout consistency check
  - Broken link detection

- **SEO Analysis**
  - Meta tags analysis
  - Image alt tags check
  - Heading structure evaluation
  - Mobile friendliness assessment

- **Performance Analysis**
  - Load time measurement
  - Performance score calculation
  - Optimization suggestions

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd website-analyzer
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Open `website_analyzer.py` and modify the URL in the `main()` function to the website you want to analyze:
```python
url = "https://your-website.com"  # Replace with your target website
```

2. Run the analyzer:
```bash
python website_analyzer.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The script will output a detailed analysis including:
- UX analysis with navigation, readability, and layout suggestions
- SEO analysis with meta tags, alt tags, and heading structure recommendations
- Performance analysis with load time and optimization suggestions

## Notes

- The performance analysis currently uses dummy data. To get real performance metrics, you'll need to implement the Google PageSpeed API.
- Make sure you have proper permissions to analyze the target website.
- Some websites may block automated analysis tools.

## Requirements

- Python 3.7+
- CrewAI
- BeautifulSoup4
- Requests
- Selenium
- WebDriver Manager

## License

MIT License 