"""Capture an actual replay response using the normal browser viewer.

No token fabrication, CAPTCHA solving service, stealth plugin or endless retry.
Playwright is an optional capture dependency, not a converter dependency.
"""
import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


async def capture(url, output, seconds):
    from playwright.async_api import async_playwright
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in {'www.duelingbook.com', 'duelingbook.com'}
            or parsed.path not in {'/replay', '/replay.php'} or not parse_qs(parsed.query).get('id')):
        raise ValueError('Supply an HTTPS DuelingBook replay URL')
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, channel='msedge')
        try:
            page = await browser.new_page()
            async with page.expect_response(lambda r: urlsplit(r.url).path == '/view-replay', timeout=seconds*1000) as pending:
                await page.goto(url, wait_until='domcontentloaded', timeout=min(seconds,20)*1000)
            response = await pending.value
            data = await response.json()
            if not isinstance(data.get('plays'), list) or not data['plays']:
                raise RuntimeError('Viewer did not return a replay: '+str(data.get('message', data.get('action'))))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'status':'captured','events':len(data['plays']),'output':str(output)}))
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--deadline',type=int,default=45)
    args = parser.parse_args()
    if not 1 <= args.deadline <= 120:
        parser.error('deadline must be between 1 and 120 seconds')
    try:
        asyncio.run(asyncio.wait_for(capture(args.url,args.output,args.deadline), timeout=args.deadline+10))
    except (Exception, KeyboardInterrupt) as error:
        parser.exit(1, f'Capture stopped: {type(error).__name__}: {error}\nUse a legitimate browser response/HAR export if verification requires interaction.\n')


if __name__ == '__main__':
    main()
