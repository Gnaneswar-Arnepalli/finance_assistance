from fastapi import FastAPI, Request
import aiohttp
import re
import logging
import string
import asyncio
from retrying import retry
from fastapi import FastAPI
from starlette.background import BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    "warning": "earning",
    "asian": "asia",
    "tatar": "tata",
    "samsun": "samsung",
    "appley": "apple"
}

def is_valid_word(word):
    return word and all(c in string.ascii_letters + string.digits for c in word.replace(".", ""))

def correct_query(query):
    query_lower = query.lower()
    for wrong, right in STT_CORRECTIONS.items():
        query_lower = query_lower.replace(wrong, right)
    return query_lower

async def fetch_yahoo_ticker(session, phrase):
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={phrase}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, headers=headers, timeout=3) as response:
            response.raise_for_status()
            data = await response.json()
            if data.get("quotes"):
                ticker = data["quotes"][0]["symbol"]
                if (not any(ticker.endswith(ext) for ext in [".SA", ".F", ".SG", ".DU"]) and 
                    not ticker.startswith("^")):
                    return ticker
            return None
    except Exception as e:
        logging.debug(f"[Ticker Search Error for {phrase}] {e}")
        return None

async def extract_tickers(query):
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

    async with aiohttp.ClientSession() as session:
        phrases = [query_cleaned] + query_words
        tasks = [fetch_yahoo_ticker(session, phrase) for phrase in phrases if is_valid_word(phrase) and phrase not in STOPWORDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, ticker in enumerate(results):
            if isinstance(ticker, str) and ticker not in tickers:
                tickers.append(ticker)
                logging.info(f"[Ticker Extraction] Resolved phrase '{phrases[idx]}' to {ticker}")

    return list(set(tickers)) if tickers else []

def extract_urls(query):
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, query)
    return [url for url in urls if not url.startswith("https://https://")]

def check_retrieval_confidence(retrieved_chunks):
    chunks = retrieved_chunks.get("chunks", []) if isinstance(retrieved_chunks, dict) else []
    logging.debug(f"[Retrieval Confidence] Retrieved chunks count: {len(chunks)}")
    return len(chunks) > 0 and not isinstance(retrieved_chunks, Exception)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def fetch_data(session, url, data, timeout):
    try:
        async with session.post(url, json=data, timeout=timeout) as response:
            response.raise_for_status()
            result = await response.json()
            logging.debug(f"[Fetch Data] Success for {url}")
            return result
    except Exception as e:
        logging.error(f"[Fetch Data Error] Request to {url} failed: {e}")
        return {"error": str(e)}

async def check_agent_health(session):
    try:
        async with session.get("http://localhost:8003/health", timeout=3) as response:
            return response.status == 200
    except Exception as e:
        logging.debug(f"[Agent Health Check Error] {e}")
        return False

@app.on_event("startup")
async def startup_event():
    async with aiohttp.ClientSession() as session:
        logging.info("[Orchestrator] Pre-warming dependencies")
        health_ok = await check_agent_health(session)
        logging.info(f"[Orchestrator] Retriever Agent health: {'OK' if health_ok else 'Failed'}")

@app.get("/health")
async def health(background_tasks: BackgroundTasks):
    async with aiohttp.ClientSession() as session:
        health_ok = await check_agent_health(session)
        status = "Orchestrator is running" if health_ok else "Orchestrator is unhealthy"
        logging.debug(f"[Orchestrator] Health check: {status}")
        return {"status": status}

@app.post("/process")
async def process_query(req: Request):
    try:
        query = (await req.json()).get("query", "")
        if not query:
            narrative = "Please provide a query."
            async with aiohttp.ClientSession() as session:
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None) if isinstance(voice_response, dict) else None
            return {"narrative": narrative, "audio_base64": audio_base64}

        tickers = await extract_tickers(query)
        logging.info(f"[Orchestrator] Extracted tickers: {tickers}")
        user_urls = extract_urls(query)

        if not tickers:
            narrative = "I'm sorry, I couldn't identify any specific stocks in your query. Could you clarify the company names or tickers?"
            async with aiohttp.ClientSession() as session:
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None) if isinstance(voice_response, dict) else None
            return {"narrative": narrative, "audio_base64": audio_base64}

        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_data(session, "http://localhost:8001/run", {"tickers": tickers}, 8),
                fetch_data(session, "http://localhost:8002/run", {"tickers": tickers}, 5),
                fetch_data(session, "http://localhost:8003/query", {"query": query, "tickers": tickers, "user_urls": user_urls}, 10),
            ]
            api_data, scrape_response, retrieved_chunks = await asyncio.gather(*tasks, return_exceptions=True)

            # Validate responses
            api_data = api_data if isinstance(api_data, dict) and "error" not in api_data else {"error": str(api_data)}
            scrape_data = scrape_response.get("articles", {"error": "Scraping failed"}) if isinstance(scrape_response, dict) else {"error": str(scrape_response)}
            retrieved_chunks = retrieved_chunks if isinstance(retrieved_chunks, dict) and "error" not in retrieved_chunks else {"chunks": [], "error": str(retrieved_chunks)}

            logging.debug(f"[Orchestrator] API data keys: {list(api_data.keys()) if isinstance(api_data, dict) else 'error'}")
            logging.debug(f"[Orchestrator] Scrape data keys: {list(scrape_data.keys()) if isinstance(scrape_data, dict) else 'error'}")
            logging.debug(f"[Orchestrator] Retrieved chunks count: {len(retrieved_chunks.get('chunks', []))}")

            valid_tickers = []
            missing_tickers = []
            for ticker in tickers:
                if ticker in api_data and api_data[ticker] and "error" not in api_data[ticker]:
                    valid_tickers.append(ticker)
                else:
                    missing_tickers.append(ticker)
                    logging.warning(f"[Orchestrator] No data for ticker {ticker}")

            if not valid_tickers:
                narrative = f"I'm sorry, I couldn't find data for the requested stocks: {', '.join(missing_tickers)}. They may be delisted or unavailable."
                voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
                audio_base64 = voice_response.get("audio_base64", None) if isinstance(voice_response, dict) else None
                return {"narrative": narrative, "audio_base64": audio_base64}

            # Unified analysis
            analysis_data = await fetch_data(
                session,
                "http://localhost:8005/analyze",
                {"api_data": api_data, "scrape_data": scrape_data, "tickers": valid_tickers, "query": query},
                5
            )
            analysis_data = analysis_data if isinstance(analysis_data, dict) and "error" not in analysis_data else {"error": str(analysis_data)}
            logging.debug(f"[Orchestrator] Analysis data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'error'}")

            # Prepare LLM input
            input_for_llm = f"""
            User Query: {query}
            📊 Market Data: {api_data}
            📰 News Articles: {scrape_data}
            📈 Analysis: {analysis_data}
            """
            if check_retrieval_confidence(retrieved_chunks):
                input_for_llm += f"\n📚 Context from Docs: {retrieved_chunks}"

            response = await fetch_data(session, "http://localhost:8004/generate", {"prompt": input_for_llm, "analysis_data": analysis_data}, 5)
            narrative = response.get("response", "LLM generation failed.") if isinstance(response, dict) else "LLM generation failed."
            logging.info(f"[Orchestrator] Narrative length: {len(narrative)} chars")

            voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
            audio_base64 = voice_response.get("audio_base64", None) if isinstance(voice_response, dict) else None

            return {"narrative": narrative, "audio_base64": audio_base64}

    except Exception as e:
        logging.error(f"[Orchestrator Process Error] {e}")
        narrative = "An error occurred while processing your query. Please try again."
        async with aiohttp.ClientSession() as session:
            voice_response = await fetch_data(session, "http://localhost:8006/speak", {"text": narrative}, 5)
            audio_base64 = voice_response.get("audio_base64", None) if isinstance(voice_response, dict) else None
        return JSONResponse(
            status_code=500,
            content={"narrative": narrative, "audio_base64": audio_base64}
        )