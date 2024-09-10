import json
from playwright.async_api import async_playwright
from datetime import datetime
import pytz
from logger import Logger


def get_current_time():
    uk_tz = pytz.timezone('Europe/London')
    return datetime.now(uk_tz).strftime('%d %B %Y, %I:%M:%S %p %Z')


def get_product_name(url):
    return ' '.join(url.split('/')[-3].split('-')).capitalize()


async def fetch_product_data(url):
    Logger.info(f'Fetching product data {url}')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60 * 1000)

        await page.wait_for_function('document.querySelector("#spartacus-app-state") !== null', timeout=60 * 1000)

        script_content = await page.evaluate('''
            () => {
                const scriptTag = document.querySelector('#spartacus-app-state');
                return scriptTag ? scriptTag.innerHTML : null;
            }
        ''')

        await browser.close()
        Logger.info('Successfully Scraped Script Content')

        product_code = url.split('/')[-1]
        product_name = get_product_name(url)

        cleaned_content = script_content.replace('&q;', '"').replace('&l;', '<').replace('&g;', '>')
        data = json.loads(cleaned_content)
        data = data['cx-state']['product']['details']

        try:
            image_url = data['entities'][product_code]['variants']['value']['images']['PRIMARY']['thumbnail']['url']
        except:
            image_url = None

        ean = data['entities'][product_code]['details']['value']['ean']
        options = \
            data['entities'][product_code]['list']['value']['baseOptions'][0][
                'options']

        options_data = []
        for option in options:
            try:
                variant_name = f"{option['variantOptionQualifiers'][0]['name']} - {option['variantOptionQualifiers'][0]['value']}"
            except:
                variant_name = product_name

            try:
                options_data.append({
                    'stockLevel': option['stock']['stockLevel'],
                    'isInStock': option['stock']['stockLevelStatus'] != 'outOfStock',
                    'stockLevelStatus': option['stock']['stockLevelStatus'],
                    'name': variant_name,
                    'url': f"https://www.superdrug.com{option['url']}"
                })
            except:
                pass

        response = {
            'ean': ean,
            'name': product_name,
            'image': image_url,
            'product_code': product_code,
            'options': options_data,
            'product_url': url
        }
        Logger.info(f'Fetched product data {url}', response)

        return response
