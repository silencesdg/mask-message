import unittest
from src.utils import load_config
import os

class TestBasic(unittest.TestCase):
    def test_config_exists(self):
        config = load_config()
        self.assertIn('nitter_instances', config)
        self.assertIn('llm_config', config)

    def test_monitor_init(self):
        from src.monitor import TwitterMonitor
        m = TwitterMonitor()
        self.assertIsNotNone(m)

    def test_analyzer_init(self):
        from src.analyzer import ETFAnalyzer
        a = ETFAnalyzer()
        self.assertIsNotNone(a)

if __name__ == '__main__':
    unittest.main()
