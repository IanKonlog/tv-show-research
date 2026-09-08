"""Browser-check the site and measure decoded resource bodies on the actual URL."""
import argparse
import json
from pathlib import Path
import urllib.request
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/site-qa'
OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8080')
parser.add_argument('--label',default='local')
args=parser.parse_args()
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width,scheme in [(1280,'light'),(390,'light'),(390,'dark'),(736,'dark')]:
        page=browser.new_page(viewport={'width':width,'height':1000},color_scheme=scheme)
        errors=[]; responses=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:responses.append(r))
        page.goto(args.url,wait_until='networkidle')
        assert page.locator('h1').inner_text()=='A taste for trouble'
        assert page.locator('#taste-map circle').count()>90
        assert 'Out There (2025)' in page.locator('#show-detail').inner_text()
        page.select_option('#show-select',label='Black Sails (2014) · favorite')
        assert 'Black Sails (2014)' in page.locator('#show-detail').inner_text()
        page.get_by_role('button',name='Kin',exact=True).click()
        assert 'Kin (2021)' in page.locator('#show-detail').inner_text()
        page.locator('#taste-map rect').hover(position={'x':60,'y':60})
        assert page.locator('#map-tooltip').is_visible()
        page.mouse.move(0,0)
        assert page.locator('a.club-badge').get_attribute('href')=='https://512kb.club/'
        metrics=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        assert metrics['scroll']<=width,metrics
        resources=[]
        for r in responses:
            assert r.status==200,(r.url,r.status)
            assert r.url.startswith(args.url),r.url
            resources.append({'url':r.url,'decoded_bytes':len(r.body())})
        total=sum(r['decoded_bytes'] for r in resources)
        assert total<100000,total
        assert not errors,errors
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(OUT/f'{args.label}-{scheme}-{width}.png'),full_page=True)
        results.append({'width':width,'scheme':scheme,'resources':resources,'total_decoded_bytes':total,'errors':errors,'overflow':False})
        page.goto(args.url+'/research.html',wait_until='networkidle')
        assert page.locator('.matrix').count()==2
        assert page.locator('h1').count()==1
        assert page.evaluate('document.documentElement.scrollWidth')<=width
        for href in ['/recommendations.csv','/theme_correlations.csv','/audit.json','/numeric_pair_counts.csv','/healthz']:
            assert page.request.get(args.url+href).status==200,href
        for forbidden in ['/server.py','/rig.yaml','/.rig.lock','/../scripts/analyze.py']:
            assert page.request.get(args.url+forbidden).status==404,forbidden
        page.close()
    page=browser.new_page(java_script_enabled=False)
    page.goto(args.url)
    assert page.get_by_text('Family. Money. Consequences.',exact=True).is_visible()
    assert page.locator('noscript').is_visible()
    page.close();browser.close()
(OUT/f'{args.label}-verification.json').write_text(json.dumps(results,indent=2))
print(json.dumps({'label':args.label,'checked_viewports':len(results),'homepage_bytes':results[0]['total_decoded_bytes'],'javascript_errors':0,'checks':'passed'},indent=2))
