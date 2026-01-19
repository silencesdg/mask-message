import time
import schedule
import argparse
import sys
from src.utils import load_config, setup_logger
from src.monitor import TwitterMonitor
from src.analyzer import ETFAnalyzer
from src.market_data import MarketData
from src.notifier import Notifier

logger = setup_logger('Main')

def job(monitor, analyzer, market_data, notifier):
    logger.info("Checking for new tweets...")
    try:
        new_tweets = monitor.fetch_tweets()
        if not new_tweets:
            logger.info("No new tweets found.")
            return

        for tweet in new_tweets:
            logger.info(f"Processing new tweet: {tweet['id']}")
            
            # 1. Analyze with LLM
            keywords = analyzer.analyze_tweet(tweet['text'])
            
            # 2. Search Etfs
            etf_results = []
            final_common_stocks = []
            
            if keywords:
                etf_candidates = market_data.search_etfs(keywords)
                # Take only top 5 ETFs
                top_etfs = etf_candidates[:5]
                
                stock_stats = {} # {code: {'name': name, 'count': 0, 'weight': 0.0}}
                
                # 3. Get Holdings for each candidate
                for etf in top_etfs:
                    holdings = market_data.get_holdings(etf['code'])
                    etf['holdings'] = holdings
                    etf_results.append(etf)
                    
                    # Accumulate stock stats for intersection
                    for h in holdings:
                        s_code = h.get('股票代码')
                        s_name = h.get('股票名称')
                        # '占净值比例' is usually a string like "10.5" or float
                        try:
                            weight = float(h.get('占净值比例', 0))
                        except:
                            weight = 0.0
                            
                        if s_code not in stock_stats:
                            stock_stats[s_code] = {'name': s_name, 'count': 0, 'total_weight': 0.0}
                        
                        stock_stats[s_code]['count'] += 1
                        stock_stats[s_code]['total_weight'] += weight
                
                # Rank stocks: primarily by count (intersection), secondarily by total weight
                ranked_stocks = sorted(
                    stock_stats.items(),
                    key=lambda x: (x[1]['count'], x[1]['total_weight']),
                    reverse=True
                )
                
                # Take top 10 common stocks
                for s_code, stats in ranked_stocks[:10]:
                    final_common_stocks.append({
                        'code': s_code,
                        'name': stats['name'],
                        'occurrence': stats['count'],
                        'total_weight': stats['total_weight']
                    })
            
            # 4. Notify - combine results
            # Wrap etf_results and common_stocks into a result object
            notifier.send_notification(tweet, {
                'etfs': etf_results,
                'common_stocks': final_common_stocks
            })
            
    except Exception as e:
        logger.error(f"Error in job loop: {e}", exc_info=True)

def main():
    parser = argparse.ArgumentParser(description='Musk Tweet Monitor')
    parser.add_argument('--dry-run', action='store_true', help='Run once and exit, do not save processed tweets (not fully implemented in submodules but main loop will exit)')
    parser.add_argument('--test-notify', action='store_true', help='Send a test notification and exit')
    args = parser.parse_args()

    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Config load failed: {e}")
        sys.exit(1)

    monitor = TwitterMonitor()
    analyzer = ETFAnalyzer()
    market_data = MarketData() # This might take a while to init if updating cache
    notifier = Notifier(config.get('wechat_webhook_url'))

    if args.test_notify:
        logger.info("Sending test notification...")
        notifier.send_notification({
            'text': '这是一条测试推文。Tesla to the moon!',
            'link': 'https://nitter.net/elonmusk/status/123456789',
            'published': 'Mon, 12 Jan 2026 12:00:00 GMT'
        }, [
            {'code': '562510', 'name': '新能源车ETF', 'match_keyword': 'Tesla', 'holdings': [{'股票名称': '宁德时代', '占净值比例': '10.0'}]}
        ])
        return

    # If dry run, we might want to just fetch current RSS and print what we WOULD do
    if args.dry_run:
        logger.info("Dry run mode: Checking once...")
        job(monitor, analyzer, market_data, notifier)
        return

    # Schedule
    interval = config.get('check_interval', 300)
    schedule.every(interval).seconds.do(job, monitor, analyzer, market_data, notifier)

    logger.info(f"Monitor started. Checking every {interval} seconds.")
    
    # Run once at startup
    job(monitor, analyzer, market_data, notifier)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
