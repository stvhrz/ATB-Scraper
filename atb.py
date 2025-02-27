from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re


def parse_products(html):
    soup = BeautifulSoup(html, "html.parser")
    product_elements = soup.select('.swiper-slide')

    for index, product in enumerate(product_elements, start=1):
        name_element = product.select_one('.catalog-item__title a')
        name = name_element.text.strip() if name_element else "Назва не знайдена"

        price_element = product.select_one('.product-price--sale .product-price__top') or \
                        product.select_one('.product-price__top')
        price = price_element.text.strip() if price_element else "Ціна не знайдена"

        grams = None
        unit = "шт"
        b_add_to_cart = product.select_one('.b-addToCart')

        if b_add_to_cart:
            data_weight = b_add_to_cart.get("data-weight")
            data_measure = b_add_to_cart.get("data-current-measure")

            if data_weight and data_measure == "weight":
                grams = float(data_weight) * 1000
                unit = "г"
            elif data_weight and data_measure == "unit":
                grams = None
                unit = "шт"

        if grams is None:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(г|g|кг|kg|л|l|мл|ml)", name, re.I)
            if match:
                value = float(match[1])
                unit_match = match[2].lower()

                if unit_match in ['кг', 'kg']:
                    value *= 1000
                    unit = "г"
                elif unit_match in ['л', 'l']:
                    value *= 1000
                    unit = "мл"
                elif unit_match in ['г', 'g']:
                    unit = "г"
                elif unit_match in ['мл', 'ml']:
                    unit = "мл"

                grams = value

        print(f"{index}. {name} - {price}, {grams if grams is not None else 'N/A'} {unit}")


options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")

service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)

url = "https://www.atbmarket.com/shop/catalog/load-products?type=economy&shop_id=101332&store_id=1154"
browser.get(url)

html = browser.page_source

parse_products(html)

browser.quit()
