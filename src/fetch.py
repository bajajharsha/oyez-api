import os
import aiohttp
import asyncio
import json
import time
from categorize import categorize_data
import uuid

BASE_URL = "https://api.oyez.org/cases"
SEMAPHORE = asyncio.Semaphore(20)                                                       # Limit the number of concurrent requests
# RATE_LIMIT_DELAY = 0.2                                                                  # Delay between requests to avoid hitting rate limits

async def fetch_json(session, url):
    """Fetch JSON data from a given URL with logging."""
    start_time = time.time()
    async with SEMAPHORE:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                # print(f"[SUCCESS] Fetched: {url} in {time.time() - start_time:.2f}s")
                return data
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            return None

# Process a single case to extract case name, facts, and advocate images.
async def process_case(session, case_url):
    start_time = time.time()
    
    # Fetch detailed case information from the first href
    case_data = await fetch_json(session, case_url)
    
    await categorize_data(case_data)

    # print(f"[COMPLETE] Processed case: {case_url} in {time.time() - start_time:.2f}s")

# Fetch case summaries for a given year and immediately process each case.
async def fetch_case_urls_and_process(session, year):
    api_url = f"{BASE_URL}?per_page=0&filter=term:{year}"
    start_time = time.time()
    case_summaries = await fetch_json(session, api_url)
    # print(f"[COMPLETE] Year: {year}, Cases: {len(case_summaries) if case_summaries else 0} in {time.time() - start_time:.2f}s")

    # Fetch detailed data for each case immediately
    if case_summaries:
        tasks = []
        for case in case_summaries:
            case_url = case.get("href")
            if case_url:
                tasks.append(process_case(session, case_url))

        # Process all cases concurrently for the year
        await asyncio.gather(*tasks)

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Fetch case summaries and process cases concurrently for each year
        for year in range(1990, 2026):
            tasks.append(fetch_case_urls_and_process(session, year))
            # await asyncio.sleep(RATE_LIMIT_DELAY)                                       # Add rate limit delay between years

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

# Run the script
start_time = time.time()
asyncio.run(main())
end_time = time.time()
print(f"Total time taken to fetch from API: {end_time - start_time:.2f}s")
