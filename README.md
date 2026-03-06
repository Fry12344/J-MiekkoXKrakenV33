# 🐙 J-MiekkoXKrakenV33 (The Phantom)

**Advanced DAST & Semantic Logic Fuzzer for Bug Bounty Hunters**

Kraken is a high-performance, asynchronous web vulnerability scanner designed to detect Syntax Anomalies (SQLi/NoSQL) and Semantic Logic Flaws (IDOR, Type Confusion, Mass Assignment) in modern web applications and APIs. 

Unlike traditional scanners that rely solely on syntax injection, Kraken mutates data structures and business logic to uncover vulnerabilities that bypass modern Web Application Firewalls (WAFs).

## 🚀 Key Features
* **Full Async Engine**: Powered by `aiohttp` and `asyncio` for blazing-fast, non-blocking crawling and fuzzing.
* **Semantic Logic Chainer**: Intelligently mutates JSON payloads to test for Business Logic Flaws.
* **Smart Browser Spoofing**: Mimics real Google Chrome headers and behavior to bypass basic WAF fingerprinting.
* **State & CSRF Aware**: Automatically identifies and protects anti-CSRF tokens/nonces from being fuzzed to maintain session validity.
* **Pattern Deduplication**: Prevents infinite crawling loops (e.g., pagination explosions) by analyzing URL parameter structures.

## 🛠️ Installation & Requirements
Requires Python 3.8+

```bash
git clone [https://github.com/YOUR-USERNAME/J-MiekkoXKrakenV33.git](https://github.com/YOUR-USERNAME/J-MiekkoXKrakenV33.git)
cd J-MiekkoXKrakenV33
pip install -r requirements.txt
