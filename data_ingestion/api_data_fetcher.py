import yfinance as yf

def get_stock_data(ticker="TSLA", period="5d"):
    stock = yf.Ticker(ticker)
    return stock.history(period=period).to_dict()