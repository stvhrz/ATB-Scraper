from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
import random


def parse_products(html):
    soup = BeautifulSoup(html, "html.parser")
    product_elements = soup.select('.swiper-slide')

    products = []
    for product in product_elements:
        name_element = product.select_one('.catalog-item__title a')
        name = name_element.text.strip() if name_element else "Назва не знайдена"

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

        products.append({
            "name": name,
            "quantity": f"{grams if grams is not None else 'N/A'} {unit}"
        })
    return products


def generate_recipes(products):
 
    categories = {
        "meat": ["курятина", "свинина", "яловичина", "ковбаса", "фарш", "м’ясо", "куриця", "індичка"],
        "vegetables": ["картопля", "морква", "цибуля", "помідор", "капуста", "перець", "огірок", "буряк", "кабачок"],
        "grains": ["рис", "гречка", "макарони", "пшоно", "вівсянка", "перловка"],
        "dairy": ["молоко", "сир", "сметана", "масло", "йогурт", "вершки"],
        "spices": ["сіль", "перець", "спеції", "приправа"],
        "other": ["яйця", "олія", "цукор", "борошно", "хліб"]
    }


    available = {cat: [] for cat in categories}
    for product in products:
        name = product["name"].lower()
        categorized = False
        for cat, items in categories.items():
            if any(item in name for item in items):
                available[cat].append(product)
                categorized = True
                break
        if not categorized:
            available["other"].append(product)  # Якщо продукт не підходить під категорії

    # Виводимо, що знайшли (для дебагу)
    print("\nДоступні продукти по категоріях:")
    for cat, items in available.items():
        if items:
            print(f"{cat}: {', '.join(p['name'] for p in items)}")


    recipes = []

    # Рецепт 1: М’ясо + овочі
    if available["meat"] and available["vegetables"]:
        meat = random.choice(available["meat"])
        veg = random.choice(available["vegetables"])
        recipes.append({
            "name": f"Тушковане {meat['name']} з {veg['name']}",
            "ingredients": [meat, veg, {"name": "Сіль", "quantity": "за смаком"}],
            "instructions": f"Обсмаж {meat['name']} на сковороді, додай {veg['name']}, туши 20 хв."
        })

    # Рецепт 2: Зернові + молочне
    if available["grains"] and available["dairy"]:
        grain = random.choice(available["grains"])
        dairy = random.choice(available["dairy"])
        recipes.append({
            "name": f"{grain['name']} з {dairy['name']}",
            "ingredients": [grain, dairy],
            "instructions": f"Звари {grain['name']}, додай {dairy['name']} і перемішай."
        })

    # Рецепт 3: Овочевий салат (будь-які 2 овочі)
    if len(available["vegetables"]) >= 1:  # Зменшено вимогу до 1 овоча
        vegs = random.sample(available["vegetables"], min(2, len(available["vegetables"]))) if len(
            available["vegetables"]) > 1 else available["vegetables"]
        recipes.append({
            "name": "Овочевий салат",
            "ingredients": vegs + [{"name": "Олія", "quantity": "1 ст.л."}],
            "instructions": f"Наріж {', '.join(v['name'] for v in vegs)}, заправ олією."
        })

    # Рецепт 4: Простий омлет (якщо є яйця або молочне)
    if "яйця" in [p["name"].lower() for p in available["other"]] or available["dairy"]:
        base = next((p for p in available["other"] if "яйця" in p["name"].lower()),
                    random.choice(available["dairy"]) if available["dairy"] else None)
        if base:
            recipes.append({
                "name": "Простий омлет",
                "ingredients": [base, {"name": "Сіль", "quantity": "за смаком"}],
                "instructions": f"Збий {base['name']}, посмаж на сковороді."
            })

    return recipes


#Selenium
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")

service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)

#URL
base_url = "https://www.atbmarket.com/shop/catalog/load-products?type=economy&shop_id=101332&store_id=1154&offset={offset}"
all_products = []
offset = 0
step = 12

while True:
    url = base_url.format(offset=offset)
    browser.get(url)
    time.sleep(2)

    html = browser.page_source
    products = parse_products(html)

    if not products:
        print("\nЗбір продуктів завершено!")
        break

    all_products.extend(products)
    print(f"\nЗібрано {len(products)} продуктів з offset={offset} (всього: {len(all_products)}):")
    for i, product in enumerate(products, start=len(all_products) - len(products) + 1):
        print(f"{i}. {product['name']} - {product['quantity']}")

    # Генерація рецептів
    recipes = generate_recipes(all_products)
    if recipes:
        print("\nМожливі рецепти на основі зібраних продуктів:")
        for i, recipe in enumerate(recipes, 1):
            print(f"\n{i}. {recipe['name']}:")
            print("Інгредієнти:")
            for ingr in recipe["ingredients"]:
                print(f"  - {ingr['name']} ({ingr['quantity']})")
            print("Інструкція:", recipe["instructions"])
    else:
        print("\nПоки що недостатньо продуктів для рецептів.")

    offset += step

browser.quit()
