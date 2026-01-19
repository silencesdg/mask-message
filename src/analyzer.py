from openai import OpenAI
import json
from src.utils import load_config, setup_logger

logger = setup_logger('ETFAnalyzer')

class ETFAnalyzer:
    def __init__(self):
        config = load_config()
        llm_conf = config.get('llm_config', {})
        self.client = OpenAI(
            base_url=llm_conf.get('api_base'),
            api_key=llm_conf.get('api_key')
        )
        self.model = llm_conf.get('model', 'gpt-3.5-turbo')

    def analyze_tweet(self, tweet_text):
        """
        Analyze tweet text and return a list of related ETF keywords.
        """
        logger.info(f"Analyzing tweet: {tweet_text[:50]}...")
        
        prompt = f"""
请分析这条马斯克的推文：
"{tweet_text}"

任务：
1. 理解推文在谈论什么（加密货币、电动车、太空探索、AI、政治、或其他）。
2. 请推断如果我要在中国A股市场投资相关的ETF，应该搜索什么关键词？
3. 请只返回最相关的3-5个中文搜索关键词。
4. 格式要求：请直接返回一个JSON数组，不要包含markdown格式或其他废话。例如：["新能源车", "电池", "宁德时代"]

如果推文完全是闲聊或无明确投资指向，请返回空数组 []。
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个精通金融投资和马斯克言论分析的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown code blocks
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            keywords = json.loads(content)
            if isinstance(keywords, list):
                logger.info(f"Extracted keywords: {keywords}")
                return keywords
            else:
                logger.warning(f"LLM returned unexpected format: {content}")
                return []
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return []
