import os
import asyncio
import aiohttp


async def fetch_page(session, url, page_number):
    """
    Fetches a single page from the given URL and saves it to a local file.
    """
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                file_path = f"downloads/ebay_page_{page_number}.html"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                print(f"Downloaded: {file_path}")
            else:
                print(f"Failed to fetch {url}: HTTP {response.status}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")


async def scrape_ebay(search_query, max_pages=200):
    """
    Scrapes eBay search results for the given query and saves the pages locally.
    """
    base_url = f"https://www.ebay.co.uk/sch/i.html?_nkw={search_query}&_sacat=0&_from=R40&_ipg=240&_pgn="
    urls = [f"{base_url}{page}" for page in range(1, max_pages + 1)]

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_page(session, url, page_number)
            for page_number, url in enumerate(urls, start=1)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    search_query = "lego"
    max_pages = 200  # Max pages is 200 before ebay blocks the request
    asyncio.run(scrape_ebay(search_query, max_pages))
