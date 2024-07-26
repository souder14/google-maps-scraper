import asyncio
import itertools
from playwright.async_api import async_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import re

# Number of concurrent workers
NUM_WORKERS = 4

@dataclass
class Business:
    """holds business data"""
    name: str = None
    rating: float = None
    reviews_count: int = None
    address: str = None
    phone_number: str = None
    status: str = None
    website: str = None

@dataclass
class BusinessList:
    """holds list of Business objects,
    and save to csv
    """
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        """transform business_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file

        Args:
            filename (str): filename
        """
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)

async def extract_business_info(listing):
    """Extract business information from a single listing"""
    business = Business()

    # Extract name
    name_element = listing.locator('.qBF1Pd')
    business.name = await name_element.inner_text() if await name_element.count() > 0 else ""

    # Extract rating and review count
    rating_element = listing.locator('.MW4etd')
    if await rating_element.count() > 0:
        business.rating = float(await rating_element.inner_text())
        reviews_count_element = listing.locator('.UY7F9')
        if await reviews_count_element.count() > 0:
            business.reviews_count = int(re.search(r'\d+', await reviews_count_element.inner_text()).group())

    # Extract address
    address_elements = listing.locator('.W4Efsd span')
    if await address_elements.count() > 2:
        business.address = (await address_elements.nth(2).inner_text()).strip()

    # Extract phone number
    phone_element = listing.locator('.UsdlK')
    business.phone_number = await phone_element.inner_text() if await phone_element.count() > 0 else ""

    # Extract status
    status_element = listing.locator('.W4Efsd span[style*="color: rgba(217,48,37,1.00);"]')
    if await status_element.count() > 0:
        business.status = await status_element.inner_text()

    # Extract website
    website_element = listing.locator('a[data-value="Website"]')
    business.website = await website_element.get_attribute('href') if await website_element.count() > 0 else ""

    return business

def get_locations():
    with open('locations.txt', 'r') as file:
        return [location.strip() for location in file.readlines()]

def get_search_terms():
    with open('terms.txt', 'r') as file:
        return [term.strip() for term in file.readlines()]

async def perform_search(context, search_query, total):
    print(f"Searching for: {search_query}")

    page = await context.new_page()
    await page.goto("https://www.google.com/maps", timeout=60000)
    await page.wait_for_timeout(5000)

    await page.locator('//input[@id="searchboxinput"]').fill(search_query)
    await page.wait_for_timeout(3000)

    await page.keyboard.press("Enter")
    await page.wait_for_timeout(5000)

    # scrolling
    await page.hover('//div[contains(@class, "Nv2PK")]')

    previously_counted = 0
    while True:
        await page.mouse.wheel(0, 10000)
        await page.wait_for_timeout(3000)

        if await page.locator('//div[contains(@class, "Nv2PK")]').count() >= total:
            listings = await page.locator('//div[contains(@class, "Nv2PK")]').all()
            listings = listings[:total]
            print(f"Total Scraped: {len(listings)}")
            break
        else:
            if await page.locator('//div[contains(@class, "Nv2PK")]').count() == previously_counted:
                listings = await page.locator('//div[contains(@class, "Nv2PK")]').all()
                print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                break
            else:
                previously_counted = await page.locator('//div[contains(@class, "Nv2PK")]').count()
                print(f"Currently Scraped: ", previously_counted)

    business_list = BusinessList()

    for listing in listings:
        try:
            business = await extract_business_info(listing)
            business_list.business_list.append(business)
        except Exception as e:
            print(f'Error occurred: {str(e)}')
    
    await page.close()
    return business_list, search_query

def load_completed_searches():
    if os.path.exists('completed_searches.txt'):
        with open('completed_searches.txt', 'r') as file:
            return set(file.read().splitlines())
    return set()

def save_completed_search(search_query):
    with open('completed_searches.txt', 'a') as file:
        file.write(f"{search_query}\n")

async def worker(context, queue, total):
    while True:
        search_query = await queue.get()
        if search_query is None:
            break
        business_list, query = await perform_search(context, search_query, total)
        
        # Save results
        search_name = query.replace(' ', '_')
        business_list.save_to_csv(f"google_maps_data_{search_name}")
        
        # Mark this search as completed
        save_completed_search(query)
        
        queue.task_done()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--total", type=int, default=120)
    parser.add_argument("-n", "--num_searches", type=int, default=None)
    args = parser.parse_args()
    
    locations = get_locations()
    terms = get_search_terms()
    
    # Create all combinations of locations and terms
    search_combinations = list(itertools.product(terms, locations))
    
    # Load completed searches
    completed_searches = load_completed_searches()
    
    # Filter out completed searches
    search_combinations = [combo for combo in search_combinations 
                           if f"{combo[0]} {combo[1]}" not in completed_searches]
    
    # If num_searches is not specified, use all remaining combinations
    if args.num_searches is None:
        args.num_searches = len(search_combinations)
    else:
        args.num_searches = min(args.num_searches, len(search_combinations))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create a queue to hold search queries
        queue = asyncio.Queue()
        
        # Add search queries to the queue
        for term, location in search_combinations[:args.num_searches]:
            await queue.put(f"{term} {location}")
        
        # Add None values to signal workers to stop
        for _ in range(NUM_WORKERS):
            await queue.put(None)
        
        # Create browser contexts and workers based on NUM_WORKERS
        contexts = [await browser.new_context() for _ in range(NUM_WORKERS)]
        workers = [asyncio.create_task(worker(context, queue, args.total)) for context in contexts]
        
        # Wait for all workers to complete
        await asyncio.gather(*workers)
        
        # Close all contexts
        for context in contexts:
            await context.close()
        
        await browser.close()

if __name__ == "__main__":
    print("###############################")
    print("####### Google Maps Scraper ####")
    print("###############################")
    asyncio.run(main())