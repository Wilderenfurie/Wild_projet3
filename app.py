import pandas as pd
import numpy as np
import requests
import streamlit as st
import yfinance as yf
from datetime import datetime

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

