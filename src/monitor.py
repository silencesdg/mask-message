import time
import random
from playwright.sync_api import sync_playwright
from src.utils import load_config, load_processed_tweets, save_processed_tweets, setup_logger

logger = setup_logger('TwitterMonitor')

class TwitterMonitor:
    def __init__(self):
        self.config = load_config()
        self.nitter_instances = self.config.get('nitter_instances', [])
        # We need to clean up nitter instances to just be the base URL
        self.nitter_instances = [url.rstrip('/') for url in self.nitter_instances]
        loaded_ids = load_processed_tweets()
        self.processed_tweets = set(loaded_ids)
        self.is_first_run = len(loaded_ids) == 0

    def get_profile_url(self, instance):
        return f"{instance}/elonmusk"

    def fetch_tweets(self):
        new_tweets = []
        # Shuffle instances to distribute load
        instances = self.nitter_instances.copy()
        random.shuffle(instances)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for instance in instances:
                url = self.get_profile_url(instance)
                logger.info(f"Trying to fetch tweets from {url}")
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                try:
                    page.goto(url, timeout=30000)
                    # Wait for timeline to load
                    page.wait_for_selector('.timeline-item', timeout=10000)
                    
                    # Get timeline items
                    timeline_items = page.query_selector_all('.timeline-item')
                    
                    if not timeline_items:
                        logger.warning(f"No timeline items found on {instance}")
                        continue

                    logger.info(f"Successfully fetched {len(timeline_items)} items from {instance}")
                    
                    # Process entries
                    for item in timeline_items[:10]:
                        link_el = item.query_selector('a.tweet-link')
                        if not link_el: continue
                        tweet_link_suffix = link_el.get_attribute('href')
                        tweet_id = tweet_link_suffix.split('/')[-1].split('#')[0]
                        
                        if tweet_id not in self.processed_tweets:
                            # It's a new tweet
                            if self.is_first_run:
                                # Silent add for first run
                                self.processed_tweets.add(tweet_id)
                                continue

                            # Normal processing
                            full_link = f"{instance}{tweet_link_suffix}"
                            content_el = item.query_selector('.tweet-content')
                            text = content_el.inner_text() if content_el else ""
                            date_el = item.query_selector('.tweet-date a')
                            published = date_el.get_attribute('title') if date_el else "Unknown time"
                            
                            replying_to_el = item.query_selector('.replying-to')
                            is_reply = replying_to_el is not None
                            
                            final_text = text
                            if is_reply:
                                logger.info(f"Tweet {tweet_id} is a reply. Fetching context...")
                                try:
                                    # Open detail page to get context
                                    # We can simply navigate the current page or open a new one. 
                                    # Let's open a new page/tab for the detail to keep timeline intact or just navigate back?
                                    # Navigating main page is fine since we are iterating elements handles matching DOM,
                                    # BUT navigating away invalidates element handles. 
                                    # So we must open a new page.
                                    detail_page = context.new_page()
                                    detail_page.goto(full_link, timeout=30000)
                                    
                                    # On detail page, find the main tweet's parent
                                    # The container is usually .conversation
                                    # The main tweet has class .main-tweet or ID 'm' sometimes
                                    # The parent is the tweet immediately preceding the main tweet in the conversation flow
                                    
                                    detail_page.wait_for_selector('.main-tweet', timeout=10000)
                                    
                                    # Strategy: Find the .main-tweet, then look for previous sibling that is a tweet-body or timeline-item?
                                    # Actually, Nitter structure:
                                    # <div class="timeline-item thread">
                                    #   <div class="timeline-item ">... parent ...</div>
                                    #   <div class="timeline-item thread-last "> ... </div>
                                    #   <div class="timeline-item main-tweet"> ... </div>
                                    # </div>
                                    # It varies. Safe bet: Look for all .timeline-item which are NOT replies to the main tweet (replies come after).
                                    # The one closely before main-tweet is the parent.
                                    
                                    # Get all timeline items in the conversation
                                    # We need to find the one where the next sibling is the main tweet?
                                    # Let's try to just grab all text from items *before* the main tweet.
                                    
                                    # Simple robust logic:
                                    # 1. Find .main-tweet
                                    # 2. Look for .tweet-content inside items that appear before it.
                                    
                                    # Using playwright evaluation to get text of the PREVIOUS timeline item
                                    parent_text = detail_page.evaluate('''() => {
                                        const main = document.querySelector('.main-tweet');
                                        if (!main) return null;
                                        // The main-tweet div itself might be a timeline-item, or wrapped.
                                        // Usually class="timeline-item main-tweet"
                                        
                                        // We want the previous sibling that is also a timeline-item (containing the parent tweet)
                                        let prev = main.previousElementSibling;
                                        while (prev && !prev.classList.contains('timeline-item')) {
                                            prev = prev.previousElementSibling;
                                        }
                                        
                                        if (prev) {
                                            const content = prev.querySelector('.tweet-content');
                                            return content ? content.innerText : null;
                                        }
                                        return null;
                                    }''')
                                    
                                    if parent_text:
                                        logger.info("Found parent tweet text.")
                                        final_text = f"Context (Parent Tweet): {parent_text}\n\nReplying: {text}"
                                    else:
                                        logger.warning("Could not find parent tweet on detail page.")
                                        # Fallback: maybe it's not in the DOM tree as sibling?
                                        # Just allow normal text.
                                    
                                    detail_page.close()
                                    
                                except Exception as e:
                                    logger.error(f"Failed to fetch context for {tweet_id}: {e}")
                                    if 'detail_page' in locals():
                                        detail_page.close()
                        
                        new_tweets.append({
                            'id': tweet_id,
                            'text': final_text,
                            'link': full_link,
                            'published': published
                        })
                        self.processed_tweets.add(tweet_id)
                    
                    if new_tweets or self.is_first_run:
                        save_processed_tweets(list(self.processed_tweets))
                    
                    # If success, break
                    break

                except Exception as e:
                    logger.error(f"Error scraping {instance}: {e}")
                    page.close()
                    continue
            
            browser.close()
                
        return new_tweets

