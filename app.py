import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup
import streamlit as st
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
    commercial_stock_api_url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/?frequency=weekly&data[0]=value&facets[series][]=WCRFPUS2&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"+api_key
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

def oil_key_indicators():
    url="https://www.investing.com/commodities/crude-oil-technical"
    navigator = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'
    html = requests.get(url, headers={'User-Agent': navigator})
    soup=BeautifulSoup(html.text, 'html.parser')
    indicators = soup.find_all('div', {"class" : "dynamic-table_dynamic-table-wrapper__MhGMX"})
    list_indicators=[]
    for i in range(len(indicators)):
        list_indicators.append(indicators[i].text)
    return list_indicators
 
#recuperation des indicators clé de investing.com
def oil_key_indicators():
   
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Exécuter en arrière-plan
    options.add_argument("--disable-blink-features=AutomationControlled")  # Désactiver la détection Selenium
    options.add_argument("--disable-dev-shm-usage")

    #Lancer Chrome avec Selenium Stealth
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    #Appliquer le mode "Stealth" pour éviter d'être détecté
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win64",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # Ouvrir la page
    driver.get("https://www.investing.com/commodities/crude-oil-technical")
    print("Page ouverte sans être détecté")

   # gestion des popup cookies
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_button.click()
        print("Cookies acceptés.")
    except:
        print("Aucune pop-up de cookies détectée.")

    # cliquer sur le bouton "Daily"
    try:
        daily_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='1d']"))
        )
        daily_button.click()
        print("Bouton 'Daily' cliqué.")
    except Exception as e:
        print(f"Erreur en cliquant sur 'Daily' : {e}")
        driver.quit()
        driver.quit()
        return pd.DataFrame()

    # Attendre que les indicateurs techniques se chargent
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dynamic-table_dynamic-table-wrapper__MhGMX"))
        )
        print("Données chargées.")
        html = driver.page_source  # Extraire le HTML mis à jour
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        driver.quit()
        return pd.DataFrame()

    driver.quit()  # Fermer proprement

    soup=BeautifulSoup(html, 'html.parser')
    indicators = soup.find_all('div', {"class" : "dynamic-table_dynamic-table-wrapper__MhGMX"})

    raw_string=indicators[1].text
    #list_indicators=[]
    #for i in range(len(indicators)):
        #list_indicators.append(indicators[i].text)
    #return list_indicators
    raw_string_cleaned = (
    raw_string.replace("Buy", "Buy ")
              .replace("Sell", "Sell ")
              .replace("Neutral", "Neutral ")
              .replace("Overbought", "Overbought ")
              .replace("Oversold", "Oversold ")
              .replace("Less Volatility", "Less Volatility ")
              .replace("High Volatility", "High Volatility ")
              .replace("NameValueAction", "")
    )

    #  Extraction avec regex
    pattern = r"([a-zA-Z0-9(),/%\- ]+?)\s*(-?\d+\.\d+|100|0)\s*(Buy|Sell|Neutral|Overbought|Oversold|Less Volatility|High Volatility)"
    matches = re.findall(pattern, raw_string_cleaned)

    #  Création du DataFrame
    df = pd.DataFrame(matches, columns=["Name", "Value", "Action"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Affichage du DataFrame final
    return df


print(oil_key_indicators())