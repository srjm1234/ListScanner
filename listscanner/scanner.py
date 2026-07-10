from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests

from listscanner.classifier import check_risk
from listscanner.models import ScanResult, ScanStats


class WebScanner:
    def __init__(self, target_url, wordlist, threads=10, timeout=5):
        self.target_url = fix_url(target_url)
        self.wordlist = wordlist
        self.threads = max(1, int(threads))
        self.timeout = float(timeout)
        self.stats = ScanStats(total=len(wordlist))

    def scan(self):
        results = []

        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            tasks = [pool.submit(self.check_path, path) for path in self.wordlist]

            for task in as_completed(tasks):
                result, state = task.result()
                if state == "found":
                    self.stats.found += 1
                    results.append(result)
                    print(f"[发现] {result.status_code}  {result.url}  {result.risk_type}/{result.risk_level}")
                elif state == "not_found":
                    self.stats.not_found += 1
                else:
                    self.stats.errors += 1

        results.sort(key=sort_result)
        return results

    def check_path(self, path):
        url = urljoin(self.target_url, path)

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=False,
                headers={"User-Agent": "ListScanner/2.0"},
            )
        except requests.RequestException:
            return None, "error"

        if response.status_code == 404:
            return None, "not_found"

        risk_type, risk_level = check_risk(path)
        result = ScanResult(
            path="/" + path.lstrip("/"),
            url=url,
            status_code=response.status_code,
            size=len(response.content),
            content_type=response.headers.get("Content-Type", ""),
            risk_type=risk_type,
            risk_level=risk_level,
        )
        return result, "found"


def fix_url(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    if not url.endswith("/"):
        url += "/"
    return url


def sort_result(result):
    risk_order = {"高风险": 0, "中风险": 1, "低风险": 2}
    return (risk_order.get(result.risk_level, 9), result.status_code, result.path)
