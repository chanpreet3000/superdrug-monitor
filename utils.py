from datetime import datetime
from typing import List, Tuple

import discord
import pytz
from Logger import Logger
import requests
from bs4 import BeautifulSoup
import json

cookies = {
    'cookie': 'cookie'
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.5',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"13575d-3DwWx3/tr8nJdLbqIxt1UGPnEpE"',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="130", "Brave";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}


def get_current_time():
    uk_tz = pytz.timezone('Europe/London')
    return datetime.now(uk_tz).strftime('%d %B %Y, %I:%M:%S %p %Z')


def get_product_name(url):
    return ' '.join(url.split('/')[-3].split('-')).capitalize()


class ProductOptions:
    def __init__(self, name: str, stock_level: int, is_in_stock: bool, stock_status: str, url: str):
        self.name = name
        self.stock_level = stock_level
        self.is_in_stock = is_in_stock
        self.stock_status = stock_status
        self.url = url


class ProductData:
    def __init__(self, ean: str, name: str, image: str, product_code: str, options: List[ProductOptions],
                 product_url: str):
        self.ean = ean
        self.name = name
        self.image = image
        self.product_code = product_code
        self.options = options
        self.product_url = product_url

    def to_dict(self):
        return {
            'ean': self.ean,
            'name': self.name,
            'image': self.image,
            'product_code': self.product_code,
            'options': [option.__dict__ for option in self.options],
            'product_url': self.product_url
        }


def get_product_data(product_data: ProductData) -> discord.Embed:
    embed = discord.Embed(title=product_data.name, url=product_data.product_url, color=0x00ff00)

    embed.add_field(
        name='Product EAN',
        value=product_data.ean,
        inline=False
    )

    for option in product_data.options:
        embed.add_field(
            name='Variant',
            value=f'[{option.name}]({option.url})',
            inline=True
        )
        embed.add_field(
            name='Stock',
            value=f"{option.stock_level} - {option.stock_status}",
            inline=True
        )
        embed.add_field(
            name='\u200b',
            value='\u200b',
            inline=False
        )

    embed.set_footer(text=f"🕒 Time: {get_current_time()} (UK)")
    return embed


def fetch_product_data(url) -> Tuple[discord.Embed, ProductData | None]:
    try:
        Logger.info(f'Fetching product data from {url}')

        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()

        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Locate the script tag with the product data
        script_tag = soup.find(id='spartacus-app-state')
        if not script_tag:
            raise Exception('Product data not found in the page')

        # Process the script content as JSON
        try:
            cleaned_content = script_tag.string.replace('&q;', '"').replace('&l;', '<').replace('&g;', '>')
            data = json.loads(cleaned_content)['cx-state']['product']['details']
        except json.JSONDecodeError:
            raise Exception('Failed to parse product JSON data')

        # Extract product details from JSON data
        product_code = url.split('/')[-1]
        product_name = get_product_name(url)

        try:
            image_url = data['entities'][product_code]['variants']['value']['images']['PRIMARY']['thumbnail']['url']
        except KeyError:
            image_url = None

        ean = data['entities'][product_code]['details']['value']['ean']
        options = data['entities'][product_code]['list']['value']['baseOptions'][0]['options']
        selected = data['entities'][product_code]['list']['value']['baseOptions'][0]['selected']
        default_stock_level = selected['stock']['stockLevel']
        default_stock_status = selected['stock']['stockLevelStatus']

        # Process each option to extract variant information
        options_data = []
        for option in options:
            try:
                variant_name = f"{option['variantOptionQualifiers'][0]['name']} - {option['variantOptionQualifiers'][0]['value']}"
            except (KeyError, IndexError):
                variant_name = product_name

            try:
                stock_level = option['stock']['stockLevel']
                stock_status = option['stock']['stockLevelStatus']
            except KeyError:
                stock_level = default_stock_level
                stock_status = default_stock_status

            options_data.append(
                ProductOptions(
                    name=variant_name,
                    stock_level=stock_level,
                    is_in_stock=stock_status != 'outOfStock',
                    stock_status=stock_status,
                    url=f"https://www.superdrug.com{option['url']}"
                )
            )

        product_data = ProductData(
            ean=ean,
            name=product_name,
            image=image_url,
            product_code=product_code,
            options=options_data,
            product_url=url
        )

        Logger.info(f'Successfully fetched product data from {url}', product_data.to_dict())
        return get_product_data(product_data), product_data
    except Exception as e:
        Logger.error(f'Error fetching product data from {url}', e)
        return discord.Embed(
            title='Error',
            description=f'Failed to fetch product data from {url}.  Please make sure the url is correct',
            color=0xff0000
        ), None
