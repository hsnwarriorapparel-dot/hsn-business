#!/usr/bin/env python3
"""Fetch questionable wave domains to classify: real gym vs software vendor/directory/federation."""
import urllib.request, re, socket
socket.setdefaulttimeout(12)

CHECKS = {
 'L717': ('my-club.it', 'http://my-club.it'),
 'L718': ('gymup-city.it', 'http://gymup-city.it'),
 'L743': ('kickboxen-in-leipzig.de', 'https://kickboxen-in-leipzig.de'),
 'L723': ('tempiodeglielfi.it', 'http://www.tempiodeglielfi.it'),
 'L786': ('inlegatum.com', 'https://inlegatum.com'),
 'L781': ('academinalegiovii.com', 'https://academinalegiovii.com'),
 'L729': ('sturmboxing.de', 'https://sturmboxing.de'),
 'L719': ('dragoblu.com', 'https://www.dragoblu.com'),
 'L784': ('fboxcv.com', 'https://fboxcv.com'),
 'L704': ('ssdmtt.it', 'https://ssdmtt.it'),
}
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for lid, (dom, url) in CHECKS.items():
    try:
        req = urllib.request.Request(url, headers=UA)
        html = urllib.request.urlopen(req).read().decode('utf-8', errors='replace')[:6000]
        title = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
        t = re.sub(r'\s+', ' ', title.group(1)).strip()[:100] if title else '(no title)'
        desc = re.search(r'name="description"\s+content="(.*?)"', html, re.I | re.S)
        d = re.sub(r'\s+', ' ', desc.group(1)).strip()[:120] if desc else ''
        text = re.sub(r'<[^>]+>', ' ', html[:4000])
        kw = [w for w in ['boxe','boxing','muay','kickbox','mma','jiu','judo','karate','taekwondo','kampfsport','pugil','software','gestione','CRM','management','vereniging','federaci','elves','elfi','roleplay','live action'] if w in text.lower()[:3500]]
        print(f"{lid} {dom}: TITLE='{t}' | kw={kw} | desc='{d}'")
    except Exception as e:
        print(f"{lid} {dom}: FETCH-FAIL {type(e).__name__} {str(e)[:60]}")
