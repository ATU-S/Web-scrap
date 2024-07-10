import requests
from bs4 import BeautifulSoup
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Function to fetch product details from Amazon
def fetch_amazon_product_details(product_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    search_url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from Amazon: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    product_details = []

    for item in soup.select('.s-main-slot .s-result-item')[:5]:
        name = item.select_one('h2 a span')
        price = item.select_one('.a-price-whole')
        link = item.select_one('h2 a')
        if name and price and link:
            product_details.append({
                'name': name.text.strip(),
                'price': price.text.strip().replace(',', ''),  # Normalize price format
                'link': 'https://www.amazon.in' + link.get('href')
            })

    return product_details

# Function to fetch product details from Flipkart
def fetch_flipkart_product_details(product_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    search_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}"
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from Flipkart: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    product_details = []

    for item in soup.select('._1AtVbE'):
        name = item.select_one('a[rel="noopener noreferrer"] .IRpwTa')
        price = item.select_one('._30jeq3')
        link = item.select_one('a[rel="noopener noreferrer"]')
        if name and price and link:
            product_details.append({
                'name': name.text.strip(),
                'price': price.text.strip().replace('₹', '').replace(',', ''),  # Normalize price format
                'link': 'https://www.flipkart.com' + link['href']
            })

    return product_details

# Function to fetch product details from eBay
def fetch_ebay_product_details(product_name):
    search_url = f"https://www.ebay.com/sch/i.html?_nkw={product_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from eBay: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    product_details = []

    for item in soup.select('.s-item')[:5]:  # Limiting to the first 5 results
        name = item.select_one('.s-item__title')
        price = item.select_one('.s-item__price')
        link = item.select_one('.s-item__link')
        if name and price and link:
            price_text = price.text
            price_value = None
            try:
                if 'to' in price_text:  # Handle price ranges
                    price_value = float(price_text.split('to')[-1].strip().replace('$', '').replace(',', ''))
                else:
                    price_value = float(price_text.strip('$').replace(',', ''))
            except ValueError:
                continue
            price_in_rupees = round(price_value * 75, 2)

            product_details.append({
                'name': name.text.strip(),
                'price': f'₹{price_in_rupees}',
                'link': link['href']
            })

    return product_details

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form['product_name']
        return redirect(url_for('results', product_name=product_name))

    return render_template('index.html')

@app.route('/results/<product_name>')
def results(product_name):
    amazon_products = fetch_amazon_product_details(product_name)
    # Add a delay to avoid hitting Flipkart too quickly after Amazon
    time.sleep(1)
    flipkart_products = fetch_flipkart_product_details(product_name)
    ebay_products = fetch_ebay_product_details(product_name)
    return render_template('results.html', amazon_products=amazon_products, flipkart_products=flipkart_products, ebay_products=ebay_products)

if __name__ == '__main__':
    app.run(debug=True)
