#returning stock information and data
import yfinance as yf

def get_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info