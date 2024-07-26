# Google Maps Scraper

## Overview

This Google Maps Scraper is a Python-based tool that uses Playwright to extract business data from Google Maps. It's designed for educational purposes and can be easily customized to suit various data collection needs.

## Features

- Extracts business information including name, rating, review count, address, phone number, status, and website
- Supports single and multiple search queries
- Concurrent scraping with multiple workers for improved efficiency
- Saves results in both CSV and Excel formats
- Resumes interrupted scraping sessions

## Installation

1. (Optional) Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install the Chromium browser for Playwright:
   ```
   playwright install chromium
   ```

## Usage

### Single Search

To perform a single search:

```
python main.py -s "search query" -t number_of_results
```

Replace "search query" with your desired search term and location, and number_of_results with the number of listings you want to scrape.

### Multiple Searches

1. Edit the `locations.txt` file to include the locations you want to search, one per line.
2. Edit the `terms.txt` file to include the search terms you want to use, one per line.
3. Run the script:
   ```
   python main.py -t number_of_results -n number_of_searches
   ```

   - `-t` specifies the number of results per search (default is 120)
   - `-n` specifies the number of searches to perform (optional, defaults to all combinations)

## Output

The scraper saves the results in the `output` directory:
- CSV files named `google_maps_data_<search_query>.csv`
- An Excel file named `google_maps_data.xlsx` (if using the Excel output option)

## Tips for Effective Searching

To bypass the 120 result limit and get more comprehensive data:

1. Use more specific and granular search queries.
2. Combine different terms with various locations.

For example, instead of a broad search like "Kyiv dentist", use multiple specific searches:
- "Kyiv dentist"
- "Lviv dentist"
- "Warszawa dentist"

## Customization

The script is designed to be easily customizable. You can modify the `Business` class in `main.py` to extract additional data fields or adjust the scraping logic as needed.

## Disclaimer

This tool is intended for educational purposes only. Ensure you comply with Google's terms of service and respect website scraping policies when using this tool.

## Contributing

Contributions to improve the scraper are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

[MIT License](LICENSE)
