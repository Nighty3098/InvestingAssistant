import json
import requests
from bs4 import BeautifulSoup
import random
import time
from typing import List, Dict

class ProxyManager:
    def __init__(self, max_proxies: int = 20, check_timeout: int = 5, storage_file: str = "proxies.json"):
        self.proxies = []
        self.max_proxies = max_proxies
        self.check_timeout = check_timeout
        self.last_update = 0
        self.update_interval = 600
        self.storage_file = storage_file
        self.sources = [
            {'url': 'https://free-proxy-list.net/', 'type': 'table'},
            {'url': 'https://www.proxy-list.download/HTTP', 'type': 'list'},
            {'url': 'https://hidemy.name/ru/proxy-list/', 'type': 'table'},
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Загружаем ранее сохраненные прокси при инициализации
        self.load_proxies_from_file()

    def fetch_proxies(self) -> List[Dict[str, str]]:
        proxies = []
        
        for source in self.sources:
            try:
                response = requests.get(source['url'], headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if source['type'] == 'table':
                    table = soup.find('table')
                    if not table:
                        continue
                        
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all('td')
                        if len(cells) >= 7:
                            ip = cells[0].text.strip()
                            port = cells[1].text.strip()
                            protocol = 'https' if 'HTTPS' in cells[6].text.upper() else 'http'
                            
                            proxies.append({
                                'ip': ip,
                                'port': port,
                                'protocol': protocol,
                                'url': f"{protocol}://{ip}:{port}",
                                'source': source['url'],
                                'last_checked': None,
                                'success_rate': 0
                            })
                
                elif source['type'] == 'list':
                    for item in soup.select('.Table'):
                        for row in item.select('tr'):
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                ip = cols[0].text.strip()
                                port = cols[1].text.strip()
                                proxies.append({
                                    'ip': ip,
                                    'port': port,
                                    'protocol': 'http',
                                    'url': f"http://{ip}:{port}",
                                    'source': source['url'],
                                    'last_checked': None,
                                    'success_rate': 0
                                })
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching from {source['url']}: {str(e)}")
        
        return proxies

    def check_proxy(self, proxy: Dict[str, str]) -> bool:
        try:
            test_url = 'https://httpbin.org/ip'
            response = requests.get(
                test_url,
                proxies={proxy['protocol']: proxy['url']},
                timeout=self.check_timeout,
                headers=self.headers
            )
            
            if response.status_code == 200:
                origin_ip = response.json().get('origin', '')
                if origin_ip == proxy['ip']:
                    proxy['last_checked'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    proxy['success_rate'] = min(proxy.get('success_rate', 0) + 10, 100)
                    return True
            return False
        except:
            proxy['success_rate'] = max(proxy.get('success_rate', 0) - 5, 0)
            return False

    def update_proxies(self):
        print("Updating proxy list...")
        candidates = self.fetch_proxies()
        random.shuffle(candidates)
        
        working_proxies = []
        for proxy in candidates:
            if len(working_proxies) >= self.max_proxies:
                break
                
            if self.check_proxy(proxy):
                working_proxies.append(proxy)
                print(f"Added working proxy: {proxy['ip']}:{proxy['port']}")
        
        # Объединяем с существующими прокси
        existing_ips = {p['ip'] for p in self.proxies}
        self.proxies = [
            p for p in self.proxies + working_proxies 
            if p['ip'] not in existing_ips
        ][:self.max_proxies]
        
        self.last_update = time.time()
        self.save_proxies_to_file()
        print(f"Proxy list updated. Total working: {len(self.proxies)}")

    def save_proxies_to_file(self):
        """Сохраняем прокси в JSON файл"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.proxies, f, indent=2)
            print(f"Proxies saved to {self.storage_file}")
        except Exception as e:
            print(f"Error saving proxies: {str(e)}")

    def load_proxies_from_file(self):
        """Загружаем прокси из JSON файла"""
        try:
            with open(self.storage_file, 'r') as f:
                self.proxies = json.load(f)
            print(f"Loaded {len(self.proxies)} proxies from {self.storage_file}")
        except FileNotFoundError:
            print("No existing proxy file found. Starting fresh.")
        except Exception as e:
            print(f"Error loading proxies: {str(e)}")

    def get_random_proxy(self) -> Dict[str, str]:
        if not self.proxies or time.time() - self.last_update > self.update_interval:
            self.update_proxies()
            
        if not self.proxies:
            raise Exception("No working proxies available")
            
        return random.choice(self.proxies)

    def get_proxy_for_requests(self) -> Dict[str, str]:
        proxy = self.get_random_proxy()
        return {
            'http': proxy['url'],
            'https': proxy['url']
        }

if __name__ == "__main__":
    pm = ProxyManager(max_proxies=10)
    
    try:
        proxy = pm.get_proxy_for_requests()
        print("Selected proxy:", proxy)
        
        response = requests.get(
            'https://httpbin.org/ip',
            proxies=proxy,
            timeout=10
        )
        print("Response:", response.json())
    except Exception as e:
        print("Error:", str(e))
