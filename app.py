import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup
import streamlit as st
import re
import nltk
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('vader_lexicon')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from playwright.async_api import async_playwright
import asyncio
import nest_asyncio
nest_asyncio.apply()

#historique quotidien du prix de vente a la cloture de crude oil wti
def oil_historical_price_api():
    historical_api_url = "https://www.alphavantage.co/query?function=WTI&interval=daily&apikey=G58HAXAGRDF1BQNL"
    result=requests.get(historical_api_url).json()
    df_historical = pd.json_normalize(result,record_path="data")
    return df_historical 

#historique quotidien du prix de vente a la cloture et volume vendu de crude oil wti
def oil_historical_price_v2():
    df_historical_v2 = yf.download('CL=F', start='1986-01-01', end=datetime.today().strftime('%Y-%m-%d'))
    return df_historical_v2

#production hebdo de crude oil wti
def oil_field_production_api():
    api_key="&api_key=4blAbaNUuijD7vmrU3MUw9BgcIdYMCs0xpxqomst"
    field_production_api_url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/?frequency=weekly&data[0]=value&facets[series][]=WCRFPUS2&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"+api_key
    result=requests.get(field_production_api_url).json()
    df_field_production = pd.json_normalize(result,record_path=["response","data"])
    return df_field_production

#stock hebdo commercial de crude oil wti
def oil_commercial_stock_api():
    api_key="&api_key=4blAbaNUuijD7vmrU3MUw9BgcIdYMCs0xpxqomst"
    commercial_stock_api_url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"+api_key
    result=requests.get(commercial_stock_api_url).json()
    df_commercial_stock =pd.json_normalize(result,record_path=["response","data"])
    return df_commercial_stock

#nombre de jours hebdo d'approvisionnement de crude oil wti
def oil_days_supply_api():
    api_key="&api_key=4blAbaNUuijD7vmrU3MUw9BgcIdYMCs0xpxqomst"
    days_supply_api_url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/?frequency=weekly&data[0]=value&facets[series][]=W_EPC0_VSD_NUS_DAYS&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"+api_key
    result=requests.get(days_supply_api_url).json()
    df_days_supply = pd.json_normalize(result,record_path=["response","data"])
    return df_days_supply


async def async_oil_key_indicators(*args, **kwargs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.tradingview.com/symbols/NYMEX-CL1!/technicals/")
        await page.wait_for_load_state("domcontentloaded")
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    indicators = soup.find_all('div', {"class": "tableWrapper-hvDpy38G"})
    if not indicators:
        raise ValueError("Aucune donnée trouvée sur la page")
    
    raw_string = indicators[0].text
    raw_string = raw_string.replace("−", "-")
    raw_string_cleaned = (
        raw_string.replace("Buy", " Buy ")
                  .replace("Sell", " Sell ")
                  .replace("Neutral", " Neutral ")
                  .replace("Overbought", " Overbought ")
                  .replace("Oversold", " Oversold ")
                  .replace("Less Volatility", " Less Volatility ")
                  .replace("High Volatility", " High Volatility ")
                  .replace("NameValueAction", "")
    )
    pattern = (
        r"([a-zA-Z0-9(),/%\- ]+?)\s*([−-]?\d+\.\d+)\s*"
        r"(Buy|Sell|Neutral|Overbought|Oversold|Less Volatility|High Volatility)"
    )
    matches = re.findall(pattern, raw_string_cleaned)
    df = pd.DataFrame(matches, columns=["Name", "Value", "Action"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    
    # Retourner un unique objet JSON contenant la liste
    return {"data": df.to_dict(orient="records")}

#@data_loader 
def oil_key_indicators(*args, **kwargs):
    result = asyncio.run(async_oil_key_indicators(*args, **kwargs))
    df = pd.DataFrame(result['data'])
    return df



  
#Web scraping & sentiment analysis à partir d'API News
# Création d'une fonction qui analyse le contenu de plusieurs sites web
def sitesweb_analyse_sentiment(url: str):
    navigator = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'
    html = requests.get(url, headers={'User-Agent': navigator})
    soup = BeautifulSoup(html.text, 'html.parser')
    for unwanted_tag in soup(['script','style','iframe','ins','advertissement','ads','ad','footer', 'header','a','menu','nav', 'aside','form', 'input', 'select']):
        unwanted_tag.decompose()
    text = soup.get_text()
    sid = SentimentIntensityAnalyzer() #Bibliothèque vaderSentiment
    sentiment_score = sid.polarity_scores(text)
    if sentiment_score['compound'] >= 0:
        return 'positif'
    else:
        return 'négatif'


# Création d'une fonction qui analyse la tendance globale avec l'API News
def apinews_tendance_globale():
    url = f"https://newsapi.org/v2/everything?q=Crude+Oil+WTI&apiKey=0ef44c92338042508e7b2ed9afc37e5b"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    analyzer = SentimentIntensityAnalyzer() #Bibliothèque vaderSentiment
    positive_count = 0
    negative_count = 0
    num_articles = 0
    for article in articles:
        title = article.get("title", "Titre non disponible")
        description = article.get("description", "")
        content = article.get("content", "")
        text_to_analyze = description if description else content
        if text_to_analyze:
            sentiment_score = analyzer.polarity_scores(text_to_analyze)
            compound_score = sentiment_score['compound']
            if compound_score > 0.1:
                positive_count += 1
            elif compound_score < -0.1:
                negative_count += 1
            num_articles += 1
    if num_articles > 0:
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "négative"
        else:
            return "équilibrée"
    else:
        return "aucun article"

# Création d'une fonction qui fait le bilan des colonnes d'un dataframe
def bilan_global(row):
    positive_count = sum([1 for sentiment in row[1:] if sentiment == "positif"])
    negative_count = sum([1 for sentiment in row[1:] if sentiment == "négatif"])
    if positive_count > negative_count:
        return "positif majoritaire"
    elif negative_count > positive_count:
        return "négatif majoritaire"
    else:
        return "bilan équilibré"

# Création d'une fonction pour créer le dataframe lié au Sentiment Analysis
def add_to_dataframe(urls):
    global df_sentiment
    sentiments = []
    date = datetime.now().strftime("%Y-%m-%d")
    for url in urls:
        sentiment = sitesweb_analyse_sentiment(url)
        sentiments.append(sentiment)
    column_names = ["Date", "EIA-TodayinEnergy", "OILPRICE-WorldNews", "CNBC-CrudeOilWTI",
                    "TRADINGECONOMICS-CrudeOilWTI", "INVESTING-CrudeOilWTI"]
    new_row = [date] + sentiments
    global_trend = apinews_tendance_globale()
    new_row.append(global_trend)
    df_new_row = pd.DataFrame([new_row], columns = column_names + ["API News"])
    df_new_row["Bilan global"] = df_new_row.apply(lambda row: bilan_global(row), axis=1)
    df_sentiment = pd.concat([df_sentiment, df_new_row], ignore_index = True)

# Application des fonctions précédentes
urls = [
    "https://www.eia.gov/todayinenergy/",
    "https://oilprice.com/Latest-Energy-News/World-News/",
    "https://www.cnbc.com/quotes/@CL.1",
    "https://tradingeconomics.com/commodity/crude-oil",
    "https://www.investing.com/commodities/crude-oil-news"
]

# Dataframe avec données numériques
df_prix_vente_alpha = oil_historical_price_api()
df_yahoo=oil_historical_price_v2()
df_production = oil_field_production_api()
df_stock = oil_commercial_stock_api()
df_supply = oil_days_supply_api()
df_indicators=oil_key_indicators()
df_sentiment = pd.DataFrame()
add_to_dataframe(urls)

print(df_prix_vente_alpha.head())
print(df_yahoo.head())
print(df_production.head())
print(df_stock.head())
print(df_supply.head())
print(df_indicators.head())
print(df_sentiment.head())

