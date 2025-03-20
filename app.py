import streamlit as st
import asyncio
import logging
from typing import List, Set
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from utils import get_sitemap_urls, normalize_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def get_unique_urls(url: str):
    """Get unique URLs from both the sitemap and internal links, handling missing sitemaps."""
    try:
        sitemap_urls = set()
        try:
            sitemap_urls = get_sitemap_urls(url)
        except Exception as e:
            logging.warning(f"No sitemap found or invalid format for {url}: {e}")
        
        internal_links = await fetch_internal_links(url)
        return list(sitemap_urls.union(internal_links)) if sitemap_urls or internal_links else [url]
    except Exception as e:
        logging.error(f"Failed to retrieve URLs: {e}")
        return [url]
async def fetch_internal_links(url: str) -> Set[str]:
    """Fetch internal links asynchronously using a web crawler."""
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)
            if result.success:
                return {link.get('href', '').strip() for link in result.links.get("internal", []) if link.get('href')}
    except Exception as e:
        logging.error(f"Error fetching internal links for {url}: {e}")
    return set()

async def get_unique_normalized_urls(url: str):
    """Fetch unique URLs and normalize them."""
    return list({normalize_url(u) for u in await get_unique_urls(url)})

async def fetch_page_content(url: str) -> str:
    """Fetch page content asynchronously using a web crawler."""
    try:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
        crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)
            if result.success:
                return result.markdown.raw_markdown
            else:
                logging.error(f"Failed to fetch content from {url}: {result.error_message}")
                return "Error: Could not fetch content."
    except Exception as e:
        logging.error(f"Exception while fetching {url}: {e}")
        return "Error: An unexpected error occurred."

async def crawl_parallel(urls: list, max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def process_url(url: str):
            async with semaphore:
                try:
                    result = await crawler.arun(url=url, config=crawl_config)
                    if result.success:
                        logging.info(f"✅ Successfully crawled: {url}")
                        results[url] = result.markdown.raw_markdown
                    else:
                        logging.warning(f"⚠️ Failed to crawl {url} - Error: {result.error_message}")
                        results[url] = "Error: Could not fetch content."
                except Exception as e:
                    logging.error(f"❌ Exception while processing {url}: {e}")
                    results[url] = "Error: An unexpected error occurred."
        
        await asyncio.gather(*[process_url(url) for url in urls])
        return results
    except Exception as e:
        logging.error(f"Critical error in crawling process: {e}")
        return {}
    finally:
        await crawler.close()

# Streamlit UI
st.title("Website Crawler")
url = st.text_input("Enter a website URL to scrape:")

if st.button("Scrape"):
    if url:
        with st.spinner("Crawling the website... Please wait."):
            urls_to_crawl = asyncio.run(get_unique_normalized_urls(url))
            page_contents = asyncio.run(crawl_parallel(urls_to_crawl))
            st.subheader("Extracted Content:")
            for sub_url, content in page_contents.items():
                st.markdown(f"### {sub_url}")
                st.text_area("", content, height=300, key=sub_url)
    else:
        st.error("Please enter a valid URL.")