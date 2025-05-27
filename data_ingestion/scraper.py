import requests
from bs4 import BeautifulSoup

def get_latest_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = [h.text for h in soup.find_all('h2')[:5]]
    return headlines