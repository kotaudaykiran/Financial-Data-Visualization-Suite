from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64
from bs4 import BeautifulSoup
import requests
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Use the Agg backend for thread-safe plotting
plt.switch_backend('Agg')

app = Flask(__name__)

# Global variable to store data
latest_data = {}

# Function to fetch and process data
def fetch_data():
    companies = {
        "HCLTECH": "HCL Technologies",
        "POWERGRID": "Power Grid Corporation",
        "TITAN": "Titan",
        "RELIANCE": "Reliance",
        "ULTRACEMCO": "Ultra Tech",
        "TATASTEEL": "Tata Steel",
        "TCS": "Tata Consultancy Services",
        "SBIN": "State Bank Of India",
        "LTIM": "LTI Mindtree",
        "M&M": "Mahindra & Mahindra",
        "COALINDIA": "Coal India",
        "GRASIM": "Grasim Industries",
        "LT": "Larsen & Turbo",
        "ADANIPORTS": "Adani Ports",
        "AXISBANK": "Axis Bank",
        "APOLLOHOSP": "Apollo Hospitals Enterprise",
        "DRREDDY": "Dr.Reddy's Laboratories",
        "MARUTI": "Maruti Suzuki",
        "BHARTIARTL": "Bharti Airtel",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "ADANIENT": "Adani Enterprises",
        "ITC": "ITC",
        "BRITANNIA": "Britannia Industries",
        "CIPLA": "Cipla",
        "NESTLEIND": "Nestle India",
        "ONGC": "Oil & Natural Gas Corpn",
        "EICHERMOT": "Eicher Motors",
        "BAJAJ-AUTO": "Bajaj Auto",
        "HDFCLIFE": "HDFC Life Insurance Company",
        "TATAMOTORS": "Tata Motors",
        "HDFCBANK": "HDFC Bank",
        "BAJAJFINSV": "Bajaj Finserv",
        "ICICIBANK": "ICICI Bank",
        "INFY": "Infosys",
        "WIPRO": "Wipro",
        "BAJFINANCE": "Bajaj Finance",
        "HEROMOTOCO": "Hero Moto Corp",
        "TECHM": "Tech Mahindra",
        "BPCL": "Bharat Petroleum Corporation",
        "HINDALCO": "Hindalco Industries",
        "HINDUNILVR": "Hindustan Unilever",
        "JSWSTEEL": "JSW Steel",
        "ASIANPAINT": "Asian Paints",
        "SUNPHARMA": "Sun Pharmaceuticals Industries",
        "UPL": "UPL",
        "TATACONSUM": "Tata Consumer Products",
        "SBILIFE": "SBI Life Insurance Company",
        "DIVISLAB": "Divis Laboratories",
        "NTPC": "NTPC",
        "INDUSINDBK": "IndusInd Bank"
    }
    data = {}
    notconsolidated = {"NESTLEIND": 1, "SBILIFE": 1}

    for val in companies:
        try:
            if val not in notconsolidated:
                url = "https://www.screener.in/company/" + val + "/consolidated/"
            else:
                url = "https://www.screener.in/company/" + val + "/"

            req = requests.get(url)
            req.raise_for_status()
            soup = BeautifulSoup(req.content, "html.parser")

            p_e_number = soup.find_all("span", class_="number")

            pros = []
            cons = []

            if soup.find("div", class_="pros"):
                pros_list = soup.find("div", class_="pros").find("ul")
                pros = pros_list.find_all("li")

            if soup.find("div", class_="cons"):
                cons_list = soup.find("div", class_="cons").find("ul")
                cons = cons_list.find_all("li")

            company = companies.get(val)
            data[company] = {}
            k = 0
            for v in p_e_number:
                k += 1
                text_value = v.text.replace(",", "").strip()
                if not text_value:  # Skip if empty value
                    text_value = "0"
                try:
                    if k == 1:
                        data[company]["market_cap"] = float(text_value)
                    elif k == 2:
                        data[company]["current_price"] = float(text_value)
                    elif k == 3:
                        data[company]["high"] = float(text_value)
                    elif k == 4:
                        data[company]["low"] = float(text_value)
                    elif k == 5:
                        data[company]["pe_ratio"] = float(text_value)
                    elif k == 6:
                        data[company]["book_value"] = float(text_value)
                    elif k == 7:
                        data[company]["dividend_yield"] = float(text_value.replace("%", ""))
                    elif k == 8:
                        data[company]["roce"] = float(text_value.replace("%", ""))
                    elif k == 9:
                        data[company]["roe"] = float(text_value.replace("%", ""))
                    else:
                        data[company]["face_value"] = float(text_value)
                except ValueError:
                    continue

            data[company]["pros"] = len(pros)
            data[company]["cons"] = -1 * len(cons)

            time.sleep(1)  # Delay to handle rate limits

        except requests.RequestException as e:
            continue
        print(val,"data collected")

    return data

# Generate plots
def create_plot(data):
    metrics = ["market_cap", "current_price", "high", "low", "pe_ratio", "book_value", "dividend_yield", "roce", "roe"]
    plots = []

    for metric in metrics:
        values = [data.get(comp, {}).get(metric, 0) for comp in data.keys()]
        plt.figure(figsize=(12, 6))
        plt.bar(data.keys(), values, color='skyblue')
        plt.xticks(rotation=90)
        plt.xlabel('Companies')
        plt.ylabel(metric.replace('_', ' ').title())
        plt.title(f'{metric.replace("_", " ").title()} of Companies')
        plt.tight_layout()

        # Save plot to BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode()
        plots.append(img_base64)

    # Better scores vs. Company
    ans = []
    for v in data:
        better = 0
        count = 0
        count += data[v].get("pe_ratio", 0)
        if 20 <= data[v].get("pe_ratio", 0) <= 25:
            better += 1
        count += (data[v].get("current_price", 0) / data[v].get("book_value", 1))
        if data[v].get("current_price", 0) / data[v].get("book_value", 1) <= 1:
            better += 1
        elif data[v].get("current_price", 0) / data[v].get("book_value", 1) <= 2:
            better += 0.66
        elif data[v].get("current_price", 0) / data[v].get("book_value", 1) <= 3:
            better += 0.33
        count += data[v].get("dividend_yield", 0)
        if 2 <= data[v].get("dividend_yield", 0) <= 6:
            count += 1
            better += 1
        count += data[v].get("roce", 0)
        if data[v].get("roce", 0) >= 20:
            better += 1
        count += data[v].get("roe", 0)
        if 15 <= data[v].get("roe", 0) <= 20:
            better += 1
        better += data[v].get("pros", 0)
        better += data[v].get("cons", 0)
        ans.append([better, count, v])

    ans.sort(reverse=True)
    sorted_companies = []
    sorted_better_scores = []
    sorted_count = []
    for val in ans:
        sorted_better_scores.append(val[0])
        sorted_count.append(val[1])
        sorted_companies.append(val[2])

    plt.figure(figsize=(12, 6))
    plt.bar(sorted_companies, sorted_better_scores, color='lightcoral')
    plt.xticks(rotation=90)
    plt.xlabel('Companies')
    plt.ylabel('Better Score')
    plt.title('Better Score of Companies')
    plt.tight_layout()

    # Save plot to BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()
    plots.append(img_base64)

    plt.figure(figsize=(12, 6))
    plt.bar(sorted_companies, sorted_count, color='lightcoral')
    plt.xticks(rotation=90)
    plt.xlabel('Companies')
    plt.ylabel('Better Score')
    plt.title('Better Count of Companies')
    plt.tight_layout()

    # Save plot to BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()
    plots.append(img_base64)

    return plots

# Fetch and update data periodically
def fetch_and_update_data():
    global latest_data
    latest_data = fetch_data()
    create_and_update_plots()

# Generate plots based on the latest data
def create_and_update_plots():
    global latest_data
    return create_plot(latest_data)

@app.route('/')
def index():
    # Fetch and update data
    fetch_and_update_data()

    # Generate plots based on updated data
    plots = create_and_update_plots()

    # Render the template and pass the plots list
    return render_template('index.html', plots=plots)

if __name__ == "__main__":
    # Set up scheduler to fetch and update data every 10 minutes
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fetch_and_update_data, trigger="interval", minutes=10)  # Fetch every 10 minutes
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=True)
