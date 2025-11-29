import json
import random
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


class ProxyManager:
    def __init__(
        self,
        max_proxies: int = 20,
        check_timeout: int = 5,
        storage_file: str = "proxies.json",
    ):
        self.proxies = []
        self.max_proxies = max_proxies
        self.check_timeout = check_timeout
        self.last_update = 0
        self.update_interval = 600  # 10 минут
        self.storage_file = storage_file
        self.sources = [
            {
                "url": "https://free-proxy-list.net/",
                "type": "table",
                "ip_col": 0,
                "port_col": 1,
                "protocol_col": 6,
                "protocol_condition": lambda x: "yes" in x.lower(),
            },
            {
                "url": "https://www.proxy-list.download/api/v1/get?type=http",
                "type": "plain",
                "split_char": ":",
            },
            {
                "url": "https://hidemy.name/ru/proxy-list/",
                "type": "table",
                "ip_col": 0,
                "port_split": True,
                "protocol_col": 3,
            },
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.load_proxies_from_file()

    def _parse_table_source(self, source, response_text):
        proxies = []
        soup = BeautifulSoup(response_text, "html.parser")
        table = soup.find("table")
        if not table:
            return proxies
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            try:
                if "free-proxy-list.net" in source["url"]:
                    if len(cells) < 8:
                        continue
                    ip = cells[0].text.strip()
                    port = cells[1].text.strip()
                    protocol = (
                        "https" if "yes" in cells[6].text.lower() else "http"
                    )
                elif "hidemy.name" in source["url"]:
                    if len(cells) < 5:
                        continue
                    ip_port = cells[0].text.strip()
                    ip, port = (
                        ip_port.split(":") if ":" in ip_port else (None, None)
                    )
                    protocol = cells[3].text.strip().lower()
                    protocol = "https" if "https" in protocol else "http"
                else:
                    continue
                proxies.append(self._make_proxy_dict(ip, port, protocol, source["url"]))
            except Exception as e:
                print(e)
                continue
        return proxies

    def _parse_plain_source(self, source, response_text):
        proxies = []
        for line in response_text.split("\n"):
            if ":" in line.strip():
                ip, port = line.strip().split(source.get("split_char", ":"))
                proxies.append(self._make_proxy_dict(ip, port, "http", source["url"]))
        return proxies

    def _make_proxy_dict(self, ip, port, protocol, url):
        return {
            "ip": ip,
            "port": port,
            "protocol": protocol,
            "url": f"{protocol}://{ip}:{port}",
            "source": url,
            "last_checked": None,
            "success_rate": 0,
        }

    def fetch_proxies(self) -> List[Dict[str, str]]:
        proxies = []
        for source in self.sources:
            try:
                response = requests.get(source["url"], headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue
                if source["type"] == "table":
                    proxies.extend(self._parse_table_source(source, response.text))
                elif source["type"] == "plain":
                    proxies.extend(self._parse_plain_source(source, response.text))
                time.sleep(2)
            except Exception as e:
                print(f"Error fetching from {source['url']}: {str(e)}")
        return proxies

    def check_proxy(self, proxy: Dict[str, str]) -> bool:
        try:
            test_url = f"{proxy['protocol']}://httpbin.org/ip"
            response = requests.get(
                test_url,
                proxies={proxy["protocol"]: proxy["url"]},
                timeout=self.check_timeout,
                headers=self.headers,
            )
            if response.status_code == 200:
                origin_ip = response.json().get("origin", "")
                if proxy["ip"] in origin_ip:
                    proxy["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    proxy["success_rate"] = min(proxy.get("success_rate", 0) + 10, 100)
                    return True
            return False
        except Exception as e:
            proxy["success_rate"] = max(proxy.get("success_rate", 0) - 5, 0)
            print(e)
            return False

    def update_proxies(self):
        print("Updating proxy list...")
        candidates = self.fetch_proxies()
        random.shuffle(candidates)

        # Проверка существующих прокси
        self.proxies = [p for p in self.proxies if self.check_proxy(p)]

        # Проверка новых кандидатов
        working_proxies = []
        for proxy in candidates:
            if len(working_proxies) + len(self.proxies) >= self.max_proxies:
                break
            if self.check_proxy(proxy):
                working_proxies.append(proxy)

        # Объединение и удаление дубликатов
        existing_ips = {p["ip"] for p in self.proxies}
        self.proxies += [p for p in working_proxies if p["ip"] not in existing_ips]
        self.proxies = self.proxies[: self.max_proxies]

        self.last_update = time.time()
        self.save_proxies_to_file()
        print(f"Proxy list updated. Total working: {len(self.proxies)}")

    def save_proxies_to_file(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.proxies, f, indent=2)
        except Exception as e:
            print(f"Error saving proxies: {str(e)}")

    def load_proxies_from_file(self):
        try:
            with open(self.storage_file, "r") as f:
                self.proxies = json.load(f)
                self.proxies = [p for p in self.proxies if self.check_proxy(p)]
        except Exception as e:
            print(e)
            self.proxies = []

    def get_random_proxy(self) -> Dict[str, str]:
        if time.time() - self.last_update > self.update_interval or not self.proxies:
            self.update_proxies()
        if not self.proxies:
            raise ValueError("No working proxies available")
        return random.choice(self.proxies)

    def get_proxy_for_requests(self) -> Dict[str, str]:
        proxy = self.get_random_proxy()
        return {"http": proxy["url"], "https": proxy["url"]}


if __name__ == "__main__":
    pm = ProxyManager(max_proxies=10)
    try:
        proxy = pm.get_proxy_for_requests()
        print("Using proxy:", proxy)
        response = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=10)
        print("Response:", response.json())
    except Exception as e:
        print("Error:", str(e))
