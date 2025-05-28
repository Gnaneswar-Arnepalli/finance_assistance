from fastapi import FastAPI, Request
import requests
import re
import logging
import string

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Known Asia tech tickers
ASIA_TECH_TICKERS = ["005930.KS", "TSM", "9988.HK", "0992.HK", "1810.HK"]  # Samsung, TSMC, Alibaba, Lenovo, Xiaomi

# Stopwords to filter generic terms
STOPWORDS = {"asia", "tech", "stocks", "today", "earnings", "surprises", "risk", "exposure", "and", "in", "shared", "text", "talks", "details", "of", "to", "up", "our", "any", "latest", "you", "may"}

# Common STT corrections
STT_CORRECTIONS = {
    "shared tech": "asia tech",
    "shared text": "asia tech",
    "text talks": "tech stocks",
    "stalk": "stock",
    "tesla.": "tesla"
}

def is_valid_word(word):
    """Check if word is valid (alphanumeric, no garbage characters)."""
    return word and all(c in string.ascii_letters + string.digits for c in word.replace(".", ""))

def correct_query(query):
    """Correct STT transcription errors."""
    query_lower = query.lower()
    for wrong, right in STT_CORRECTIONS.items():
        query_lower = query_lower.replace(wrong, right)
    return query


def extract_tickers(query):
    """Extract tickers or company names from query."""
    query_lower = correct_query(query)
    query_words = query_lower.split()
    tickers = []

    # Skip casual or nonsense queries
    if "how are you" in query_lower or len([w for w in query_words if is_valid_word(w)]) < 2:
        logging.info(f"[Ticker Extraction] Skipping invalid query: {query}")
        return []

    # Use Asia tech tickers for relevant queries
    if "asia tech" in query_lower:
        logging.info("[Ticker Extraction] Using predefined Asia tech tickers")
        return ASIA_TECH_TICKERS

    # Known company name mappings
    company_map = {
        "tesla": "TSLA",
        "apple": "AAPL",
        "samsung": "005930.KS",
        "tsmc": "TSM"
    }

    for word in query_words:
        if not is_valid_word(word) or word in STOPWORDS:
            continue
        if word in company_map:
            tickers.append(company_map[word])
            logging.info(f"[Ticker Extraction] Mapped {word} to {company_map[word]}")
            continue
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={word}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("quotes"):
                ticker = data["quotes"][0]["symbol"]
                if (ticker not in tickers and 
                    not any(ticker.endswith(ext) for ext in [".SA", ".F", ".SG", ".DU"]) and 
                    not ticker.startswith("^")):  # Exclude funds, foreign listings, indices
                    tickers.append(ticker)
                logging.info(f"[Ticker Extraction] Resolved {word} to {ticker}")
        except Exception as e:
            logging.error(f"[Ticker Search Error for {word}] {e}")
            # Fallback for known companies
            if word in company_map:
                tickers.append(company_map[word])
                logging.info(f"[Ticker Extraction] Fallback mapped {word} to {company_map[word]}")

    return list(set(tickers)) if tickers else []

def extract_urls(query):
    """Extract valid URLs from query."""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, query)
    return [url for url in urls if not url.startswith("https://https://")]

def check_retrieval_confidence(retrieved_chunks):
    """Check if retrieved chunks are relevant."""
    chunks = retrieved_chunks.get("chunks", [])
    logging.info(f"[Retrieval Confidence] Retrieved chunks: {chunks}")
    return len(chunks) > 0 and "error" not in retrieved_chunks

@app.post("/process")
async def process_query(req: Request):
    query = (await req.json()).get("query", "")
    if not query:
        return {"narrative": "Please provide a query.", "audio_base64": None}

    tickers = extract_tickers(query)
    logging.info(f"[Orchestrator] Extracted tickers: {tickers}")
    user_urls = extract_urls(query)

    # Check for vague queries
    if not tickers and not any(word in query.lower() for word in ["tesla", "apple", "samsung", "tsmc"]):
        narrative = "I'm sorry, I couldn't identify any specific stocks in your query. Could you clarify the company names or tickers?"
        try:
            voice_response = requests.post(
                "http://localhost:8006/speak",
                json={"text": narrative},
                timeout=20
            ).json()
            audio_base64 = voice_response.get("audio_base64")
        except Exception as e:
            audio_base64 = None
        return {"narrative": narrative, "audio_base64": audio_base64}

    # Fetch API data
    try:
        api_data = requests.post("http://localhost:8001/run", json={"tickers": tickers}, timeout=10).json()
    except Exception as e:
        api_data = {"error": f"API Agent failed: {e}"}
    logging.info(f"[Orchestrator] API data: {api_data}")

    # Fetch scraped news
    try:
        scrape_data = requests.post("http://localhost:8002/run", json={"tickers": tickers}, timeout=30).json()["articles"]
    except Exception as e:
        scrape_data = {"error": f"Scraping Agent failed: {e}"}
    logging.info(f"[Orchestrator] Scrape data: {scrape_data}")

    # Fetch retrieved chunks
    try:
        retrieved_chunks = requests.post(
            "http://localhost:8003/query",
            json={"query": query, "tickers": tickers, "user_urls": user_urls},
            timeout=30
        ).json()
    except Exception as e:
        retrieved_chunks = {"error": f"Retriever Agent failed: {e}"}
    logging.info(f"[Orchestrator] Retrieved chunks: {retrieved_chunks}")

    # Fallback for low-confidence retrieval or timeout
    if not check_retrieval_confidence(retrieved_chunks) and tickers:
        logging.info("[Orchestrator] Using fallback analysis with API and scrape data")
        try:
            analysis_data = requests.post(
                "http://localhost:8005/analyze",
                json={"api_data": api_data, "scrape_data": scrape_data, "tickers": tickers, "query": query},
                timeout=10
            ).json()
        except Exception as e:
            analysis_data = {"error": f"Analysis Agent failed: {e}"}
        logging.info(f"[Orchestrator] Analysis data: {analysis_data}")

        # Generate narrative
        input_for_llm = f"""
        User Query: {query}
        📊 Market Data: {api_data}
        📰 News Articles: {scrape_data}
        📈 Analysis: {analysis_data}
        """
    else:
        if not tickers:
            narrative = "I'm sorry, I couldn't find enough relevant information. Could you clarify or specify the stocks or time period?"
            try:
                voice_response = requests.post(
                    "http://localhost:8006/speak",
                    json={"text": narrative},
                    timeout=20
                ).json()
                audio_base64 = voice_response.get("audio_base64")
            except Exception as e:
                audio_base64 = None
            return {"narrative": narrative, "audio_base64": audio_base64}

        # Analyze data
        try:
            analysis_data = requests.post(
                "http://localhost:8005/analyze",
                json={"api_data": api_data, "scrape_data": scrape_data, "tickers": tickers, "query": query},
                timeout=10
            ).json()
        except Exception as e:
            analysis_data = {"error": f"Analysis Agent failed: {e}"}
        logging.info(f"[Orchestrator] Analysis data: {analysis_data}")

        # Generate narrative
        input_for_llm = f"""
        User Query: {query}
        📊 Market Data: {api_data}
        📰 News Articles: {scrape_data}
        📚 Context from Docs: {retrieved_chunks}
        📈 Analysis: {analysis_data}
        """

    try:
        response = requests.post(
            "http://localhost:8004/generate",
            json={"prompt": input_for_llm, "analysis_data": analysis_data},
            timeout=20
        )
        narrative = response.json().get("response", "LLM generation failed.")
    except Exception as e:
        narrative = f"Language Agent failed: {e}"

    # Generate voice output
    try:
        voice_response = requests.post(
            "http://localhost:8006/speak",
            json={"text": narrative},
            timeout=20
        ).json()
        audio_base64 = voice_response.get("audio_base64")
    except Exception as e:
        audio_base64 = None

    return {"narrative": narrative, "audio_base64": audio_base64}