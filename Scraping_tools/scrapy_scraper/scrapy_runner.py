import multiprocessing
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _run_spider_process(url, selector, result_queue):
    """
    This function runs in a brand-new OS process (via multiprocessing.Process),
    so it gets its own fresh Python interpreter and, crucially, its own fresh
    Twisted reactor. That's what lets us call CrawlerProcess.start() every
    single time without hitting ReactorNotRestartable.
    """
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from spiders.generic_spider import GenericSpider

    settings = get_project_settings()
    settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    settings.set('ROBOTSTXT_OBEY', False)
    settings.set('LOG_LEVEL', 'INFO')

    GenericSpider.results = []

    process = CrawlerProcess(settings)
    process.crawl(GenericSpider, url=url, selector=selector)
    process.start()  # blocks until crawl finishes, safe because this is a fresh process

    result_queue.put(GenericSpider.results[0] if GenericSpider.results else None)


class ScrapyRunner:
    def scrape_single(self, url, selector=None):
        # 'spawn' gives a clean interpreter (safer than 'fork' with Twisted/Scrapy)
        ctx = multiprocessing.get_context('spawn')
        result_queue = ctx.Queue()

        p = ctx.Process(target=_run_spider_process, args=(url, selector, result_queue))
        p.start()
        p.join(timeout=60)  # adjust timeout to whatever's reasonable for your scrapes

        if p.is_alive():
            p.terminate()
            p.join()
            raise TimeoutError(f"Scrape of {url} timed out")

        if p.exitcode != 0:
            raise RuntimeError(f"Spider process exited with code {p.exitcode}")

        return result_queue.get() if not result_queue.empty() else None