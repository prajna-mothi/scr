import os
import requests

from xml.etree import ElementTree
from typing import List, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from cachetools import TTLCache, cached

#from google.cloud import secretmanager
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# wcd_url = os.getenv("WCD_URL")
# wcd_api_key = os.getenv("WCD_API_KEY")

# @dataclass
# class ProcessedChunk:
#     url: str
#     content: str
#     chunk_size: int



# # Initialize cache (stores secrets for 1 hour)
# cache = TTLCache(maxsize=1024, ttl=3600)

# @cached(cache)
# def access_secret_version(secret_id: str, version_id="latest") -> str:
#     """
#     Retrieves a secret from Google Secret Manager with caching.

#     Args:
#         secret_id (str): The name of the secret.
#         version_id (str, optional): The version of the secret to retrieve. Defaults to "latest".

#     Returns:
#         str: The secret value or None if retrieval fails.
#     """
#     try:
#         client = secretmanager.SecretManagerServiceClient()
#         project_id = os.getenv("GCP_PROJECT_ID", "hyperchat-staging-ark")  # Use environment variable or fallback

#         # Construct the secret path
#         name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

#         # Retrieve the secret
#         response = client.access_secret_version(name=name)
#         secret_value = response.payload.data.decode("UTF-8")
        
#         logging.info(f"✅ Successfully retrieved secret: {secret_id}")
#         return secret_value

#     except Exception as e:
#         logging.error(f"❌ Failed to access secret {secret_id}: {e}")
#         return None  # Return None to handle errors gracefully



  


def get_sitemap_urls(url: str) -> Set[str]:
    """Fetch URLs from a website's sitemap."""
    try:
        response = requests.get(f"{url.rstrip('/')}/sitemap.xml", timeout=5)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        return {loc.text.strip() for loc in root.findall('.//ns:loc', namespace) if loc.text} or \
               {loc.text.strip() for loc in root.findall('.//loc') if loc.text}
    except requests.RequestException:
        return set()

def normalize_url(url: str) -> str:
    """Normalize a URL by enforcing HTTPS, removing 'www', and stripping trailing slashes."""
    parsed = urlparse(url.lower().strip())
    return urlunparse(("https", parsed.netloc.lstrip("www."), parsed.path.rstrip("/"), "", "", ""))

# def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
#     """Split text into chunks, respecting code blocks and paragraphs."""
#     chunks = []
#     start = 0
#     text_length = len(text)

#     while start < text_length:
#         # Calculate end position
#         end = start + chunk_size

#         # If we're at the end of the text, just take what's left
#         if end >= text_length:
#             chunks.append(text[start:].strip())
#             break

#         # Try to find a code block boundary first (```)
#         chunk = text[start:end]
#         code_block = chunk.rfind('```')
#         if code_block != -1 and code_block > chunk_size * 0.3:
#             end = start + code_block

#         # If no code block, try to break at a paragraph
#         elif '\n\n' in chunk:
#             # Find the last paragraph break
#             last_break = chunk.rfind('\n\n')
#             if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
#                 end = start + last_break

#         # If no paragraph break, try to break at a sentence
#         elif '. ' in chunk:
#             # Find the last sentence break
#             last_period = chunk.rfind('. ')
#             if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
#                 end = start + last_period + 1

#         # Extract chunk and clean it up
#         chunk = text[start:end].strip()
#         if chunk:
#             chunks.append(chunk)

#         # Move start position for next chunk
#         start = max(start + 1, end)

#     return chunks









