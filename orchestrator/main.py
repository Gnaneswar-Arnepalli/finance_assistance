from fastapi import FastAPI, Request
import requests
import re
import logging
import string
import asyncio
import aiohttp
from retrying import retry

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Known Asia tech tickers
ASIA_TECH_TICKERS = ["005930.KS", "TSM", "9988.HK", "0992.HK", "1810.HK"]

# Stopwords to filter generic terms
STOPWORDS = {"asia", "tech", "stocks", "today", "earnings", "surprises", "risk", "exposure", "and", "in", "shared", "text", "talks", "details", "of", "to", "up", "our", "any", "latest", "you", "may", "what", "about", "the", "need", "a", "strong", "put", "land", "stokes", "for", "surerning", "highlights", "warning", "give", "me"}

# Common STT corrections
STT_CORRECTIONS = {
    "shared tech": "asia tech",
    "shared text": "asia tech",
    "text talks": "tech stocks",
    "stalk": "stock",
    "tesla.": "tesla",
    "appy": "apple",
    "stokes": "stocks",
    "talk": "stock",
    "surerning": "surprising",
    "aca text talk": "asia tech stock",
    "warning": "earning"
}

def is_valid_word(word):
    return word and all(c in string.ascii_letters + string.digits for c in word.replace(".", ""))

def correct_query(query):
    query_lower = query.lower()
    for wrong, right in STT_CORRECTIONS.items():
        query_lower = query_lower.replace(wrong, right)
    return query_lower

def extract_tickers(query):
    query_lower = correct_query(query)
    query_words = query_lower.split()
    tickers = []

    if "how are you" in query_lower or len([w for w in query_words if is_valid_word(w)]) < 2:
        logging.info(f"[Ticker Extraction] Skipping invalid query: {query}")
        return []

    if "asia tech" in query_lower:
        logging.info("[Ticker Extraction] Using predefined Asia tech tickers")
        return ASIA_TECH_TICKERS

    company_map = {
        "tesla": "TSLA",
        "apple": "AAPL",
        "samsung": "005930.KS",
        "tsmc": "TSM",
        "tata": "TATASTEEL.NS",
        "tatasteel": "TATASTEEL.NS",
        "tata stocks": "TATASTEEL.NS",
        "zerodha": "LIQUIDCASE.NS",
        "mirra stock": "MIRA",
        "natal soft": "NTES"
    }

    query_cleaned = " ".join([w for w in query_words if w not in STOPWORDS])
    found_tickers = []
    for key in company_map:
        if key in query_cleaned:
            found_tickers.append(company_map[key])
            logging.info(f"[Ticker Extraction] Mapped '{key}' to {company_map[key]}")

    if found_tickers:
        return list(set(found_tickers))

    phrases = [query_cleaned] + query_words
    for phrase in phrases:
        if not is_valid_word(phrase) or phrase in STOPWORDS:
            continue
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={phrase}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=3)
            response.raise_for_status()
            data = response.json()
            if data.get("quotes"):
                ticker = data["quotes"][0]["symbol"]
                if (ticker not in tickers and 
                    not any(ticker.endswith(ext) for ext in [".SA", ".F", ".SG", ".DU"]) and 
                    not ticker.startswith("^")):
                    tickers.append(ticker)
                    logging.info(f"[Ticker Extraction] Resolved '{phrase}' to {ticker}")
        except Exception as e:
            logging.error(f"[Ticker Search Error for {phrase}] {e}")

    return list(set(tickers)) if tickers else []

def extract_urls(query):
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, query)
    return [url for url in urls if not url.startswith("https://https://")]

def check_retrieval_confidence(retrieved_chunks):
    chunks = retrieved_chunks.get("chunks", [])
    logging.info(f"[Retrieval Confidence] Retrieved chunks: {chunks}")
    return len(chunks) > 0 and "error" not in retrieved_chunks

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def fetch_data(session, url, data, timeout):
    try:
        async with session.post(url, json=data, timeout=timeout) as response:
            response.raise_for_status()
            result = await response.json()
            logging.info(f"[Fetch Data] Success for {url}: {result}")
            return result
    except Exception as e:
        logging.error(f"[Fetch Data Error] Request to {url} failed: {e}")
        return {"error": f"Request to {url} failed: {e}"}

@app.get("/health")
async def health():
    return {"status": "Orchestrator is running"}

@app.post("/process")
async def process_query(req: Request):
    query = (await req.json()).get("query", "")
    if not query:
        narrative = "Please provide a query."
        try:
            async with aiohttp.ClientSession() as session:
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None)
        except Exception as e:
            logging.error(f"[Voice Agent Error] {e}")
            audio_base64 = None
        return {"narrative": narrative, "audio_base64": audio_base64}

    tickers = extract_tickers(query)
    logging.info(f"[Orchestrator] Extracted tickers: {tickers}")
    user_urls = extract_urls(query)

    if not tickers:
        narrative = "I'm sorry, I couldn't identify any specific stocks in your query. Could you clarify the company names or tickers?"
        try:
            async with aiohttp.ClientSession() as session:
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None)
        except Exception as e:
            logging.error(f"[Voice Agent Error] {e}")
            audio_base64 = None
        return {"narrative": narrative, "audio_base64": audio_base64}

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_data(session, "http://localhost:8001/run", {"tickers": tickers}, 8),
            fetch_data(session, "http://localhost:8002/run", {"tickers": tickers}, 5),
            fetch_data(session, "http://localhost:8003/query", {"query": query, "tickers": tickers, "user_urls": user_urls}, 10),
        ]
        api_data, scrape_response, retrieved_chunks = await asyncio.gather(*tasks, return_exceptions=True)

    logging.info(f"[Orchestrator] API data: {api_data}")
    scrape_data = scrape_response.get("articles", {"error": "Scraping failed"}) if isinstance(scrape_response, dict) else {"error": str(scrape_response)}
    logging.info(f"[Orchestrator] Scrape data: {scrape_data}")
    logging.info(f"[Orchestrator] Retrieved chunks: {retrieved_chunks}")

    valid_tickers = []
    missing_tickers = []
    for ticker in tickers:
        if isinstance(api_data, dict) and ticker in api_data and api_data[ticker] and "error" not in api_data[ticker]:
            valid_tickers.append(ticker)
        else:
            missing_tickers.append(ticker)
            logging.warning(f"[Orchestrator] No data for ticker {ticker}")

    if not valid_tickers:
        narrative = f"I'm sorry, I couldn't find data for the requested stocks: {', '.join(missing_tickers)}. They may be delisted or unavailable."
        try:
            async with aiohttp.ClientSession() as session:
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None)
        except Exception as e:
            logging.error(f"[Voice Agent Error] {e}")
            audio_base64 = None
        return {"narrative": narrative, "audio_base64": audio_base64}

    if missing_tickers:
        logging.warning(f"[Orchestrator] Missing data for tickers: {missing_tickers}")

    if not check_retrieval_confidence(retrieved_chunks):
        logging.info("[Orchestrator] Using fallback analysis with API and scrape data")
        async with aiohttp.ClientSession() as session:
            analysis_data = await fetch_data(
                session,
                "http://localhost:8005/analyze",
                {"api_data": api_data, "scrape_data": scrape_data, "tickers": valid_tickers, "query": query},
                5
            )
        logging.info(f"[Orchestrator] Analysis data: {analysis_data}")

        input_for_llm = f"""
        User Query: {query}
        📊 Market Data: {api_data}
        📰 News Articles: {scrape_data}
        📈 Analysis: {analysis_data}
        """
    else:
        async with aiohttp.ClientSession() as session:
            analysis_data = await fetch_data(
                session,
                "http://localhost:8005/analyze",
                {"api_data": api_data, "scrape_data": scrape_data, "tickers": valid_tickers, "query": query},
                5
            )
        logging.info(f"[Orchestrator] Analysis data: {analysis_data}")

        input_for_llm = f"""
        User Query: {query}
        📊 Market Data: {api_data}
        📰 News Articles: {scrape_data}
        📚 Context from Docs: {retrieved_chunks}
        📈 Analysis: {analysis_data}
        """

    async with aiohttp.ClientSession() as session:
        response = await fetch_data(session, "http://localhost:8004/generate", {"prompt": input_for_llm, "analysis_data": analysis_data}, 5)
        narrative = response.get("response", "LLM generation failed.")
        logging.info(f"[Orchestrator] Narrative: {narrative}")

    try:
        async with aiohttp.ClientSession() as session:
            voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
            audio_base64 = voice_response.get("audio_base64", None)
    except Exception as e:
        logging.error(f"[Voice Agent Error] {e}")
        audio_base64 = None

    return {"narrative": narrative, "audio_base64": audio_base64}