"""
@project:proxy_twisted
@author: momentum
@time:20191120
"""

# Enable and configure crawler
CRAWLER_CLS = 'proxy_twisted.crawler.BaseCrawler'
CRAWLER_IDLE = 300

# Enable and configure crawler engine and relevant component
ENGINE_CLS = 'proxy_twisted.crawler.engine.Engine'
ENGINE_CONFIG = {
    'downloader': 'proxy_twisted.crawler.downloader.Downloader',
    'checker': 'proxy_twisted.crawler.pipelines.CPipeline',
    'pipeline': 'proxy_twisted.crawler.pipelines.MysqlPipeline',
    'scheduler': 'proxy_twisted.crawler.scheduler.Scheduler',
    'signal': 'pydispatch.dispatcher',
    'concurrent': 1
}
# Configure crawler scheduler

# Configure crawler downloader
DOWNLOADER_CONFIG = {
    'delay': 30
}
# Configure crawler pipeline

# Enable and configure crawler spider
SPIDER_CLS = 'proxy_twisted.crawler.spiders.IPHaiSpider'


# Enable and configure detector
DETECTOR_CLS = 'proxy_twisted.detector.BaseDetector'
DETECTOR_CONFIG = {
    'c': 'proxy_twisted.detector.checker.BaseChecker'
}

# Enable and configure server
SERVER_CLS = 'proxy_twisted.server.server.Server'
CHECKER_CLS = 'proxy_twisted.detector.checker.BaseChecker'

# Configure IP pool
CAPACITY = 40

