from app.core.logger import get_logger
from app.core.config import settings
from app.models.schemas import AnalyzeEntityRequest, AnalyzeEntityResponse, GetUrlContentResponse
import os
import requests
import trafilatura
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from googlenewsdecoder import new_decoderv1 as gnewsdecoder

logger = get_logger(__name__)

class CustomerService:
    """
    Service class for customer analysis operations.
    Handles the business logic for analyzing entities.
    """

    def __init__(self):
        # All analysis is now performed by the LLM
        pass

    def analyze_entity(self, request: AnalyzeEntityRequest) -> AnalyzeEntityResponse:
        """
        Analyze the entity based on name, description, and country.
        Optionally fetch article content from URL and use LLM for analysis.
        All analysis is performed by the LLM based on the provided context.

        Args:
            request: The analysis request containing entity details.

        Returns:
            AnalyzeEntityResponse: The analysis result from LLM.
        """
        logger.info(f"Starting analysis for entity: {request.entity_name} from {request.country}")

        content = ""
        date = ""
        # if a URL is provided, fetch article
        if request.url:
            logger.info(f"Fetching article from URL: {request.url}")
            content, date = self.fetch_article(request.url)
            logger.info(f"Fetched content length: {len(content) if content else 0} characters")

        # Call LLM to analyze all information
        logger.info("Calling LLM for analysis")
        llm_result = self._call_llm(
            entity_name=request.entity_name,
            entity_description=request.entity_description,
            country=request.country,
            article_content=content
        )

        # Extract values from LLM result
        matching_score = llm_result.get("matching_score", 0)
        involved_in_criminal = llm_result.get("involved_in_criminal_activity", False)
        involved_in_fraud = llm_result.get("involved_in_monetary_fraud", False)

        logger.info(f"LLM Analysis Result - Score: {matching_score}, Criminal: {involved_in_criminal}, Fraud: {involved_in_fraud}")

        response = AnalyzeEntityResponse(
            matching_score=matching_score,
            involved_in_criminal_activity=involved_in_criminal,
            involved_in_monetary_fraud=involved_in_fraud,
            content=content,
            date=date
        )

        logger.info(f"Analysis completed for entity: {request.entity_name}")
        return response

    def _call_llm(self, entity_name: str, entity_description: str, country: str, article_content: str = "") -> dict:
        """
        Send entity information and article content to the Gemini LLM for risk analysis.
        Uses native JSON mode for efficient parsing and highly strict Adverse Media 
        prompts to accurately flag allegations and civil lawsuits.
        """
        # Note: make sure 'settings' is imported or available in your class context
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set; using default values")
            return {
                "matching_score": 50,
                "involved_in_criminal_activity": False,
                "involved_in_monetary_fraud": False,
            }

        try:
            genai.configure(api_key=api_key)
            
            # 1. Configure the model for analytical tasks
            generation_config = {
                "temperature": 0.1,  # Low temperature makes the model analytical and less "creative"
                "response_mime_type": "application/json", # Forces the API to return pure JSON (no markdown)
            }
            
            # 2. Fully disable safety blocks since we are intentionally analyzing crime/fraud
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            # 3. Define a persona to improve accuracy
            system_instruction = (
                "You are an expert KYC/AML compliance analyst. Your job is strict entity resolution "
                "and risk assessment. You must carefully distinguish the Target Entity from other "
                "people or companies mentioned in the text."
            )

            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=system_instruction
            )

            # 4. Use an "Adverse Media" prompt that flags allegations and lawsuits
            prompt = f"""
            Target Entity Information:
            - Name: {entity_name}
            - Description: {entity_description}
            - Country: {country}

            Article Content:
            {article_content[:7000] if article_content else "No article provided."}

            Task Instructions:
            1. Entity Resolution: Read the article and determine if the Target Entity is the EXACT SAME entity being discussed.
            2. Adverse Media & Risk Assessment: If the entity matches, analyze the text for any Adverse Media (Negative News). 
               - You MUST flag the entity if they are accused, sued, investigated, or charged, even if they are not convicted.
               - Civil lawsuits regarding securities, stocks, or financial misrepresentation count as monetary fraud risk.

            Output EXACTLY in this JSON schema:
            {{
                "matching_score": integer (0 to 100. 100 if the article is clearly about this exact entity. 0 if no article is provided or it's a different person),
                "involved_in_criminal_activity": boolean (true if the article mentions arrests, criminal charges, or illegal syndicates related to the entity),
                "involved_in_monetary_fraud": boolean (true if the article mentions the entity in relation to securities fraud, financial lawsuits, scams, SEC/regulatory investigations, or withholding financial disclosures)
            }}
            """

            logger.info(f"Calling Gemini API for entity: {entity_name}")
            response = model.generate_content(prompt)
            
            # 5. Parse the guaranteed JSON response
            # Because we used response_mime_type="application/json", we no longer need regex!
            result = json.loads(response.text)
            
            parsed_result = {
                "matching_score": int(result.get("matching_score", 50)),
                "involved_in_criminal_activity": bool(result.get("involved_in_criminal_activity", False)),
                "involved_in_monetary_fraud": bool(result.get("involved_in_monetary_fraud", False)),
            }
            
            logger.info(f"Successfully analyzed {entity_name}. Result: {parsed_result}")
            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON (this shouldn't happen with JSON mode): {e}")
            return {}
        except Exception as e:
            logger.error(f"LLM call failed for {entity_name}: {str(e)}")
            return {}
    
    def fetch_article(self, url: str) -> tuple[str, str]:
        """
        Decodes Google News encrypted URLs, bypasses bot protections, 
        and extracts the article text using trafilatura.
        """
        # 1. Crack the Google News URL to get the real destination
        if "news.google.com/rss/articles" in url:
            try:
                decoded_data = gnewsdecoder(url)
                if decoded_data.get("status"):
                    url = decoded_data["decoded_url"]
                    print(f"Decoded Google link to real URL: {url}")
                else:
                    print(f"Failed to decode Google News link: {decoded_data.get('message')}")
                    return "", ""
            except Exception as e:
                print(f"Error decoding Google URL: {e}")
                return "", ""

        # 2. Look like a real browser to the destination site
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            # 3. Download the HTML from the REAL website
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to fetch {url}. Status code: {response.status_code}")
                return "", ""
                
            downloaded_html = response.text
            
            # 4. Extract the clean text
            text_content = trafilatura.extract(downloaded_html)
            if not text_content:
                text_content = ""
                
            # 5. Extract the metadata (date)
            metadata = trafilatura.extract_metadata(downloaded_html)
            
            date_str = ""
            if metadata and metadata.date:
                date_str = str(metadata.date)
                
            return text_content, date_str
            
        except Exception as e:
            print(f"An error occurred while scraping {url}: {e}")
            return "", ""
        
    def get_entity_articles(self, entity: str, country: str, max_results: int = 10) -> GetUrlContentResponse:
        """
        Fetches news article links about a specific entity in a specific country 
        directly from Google News using pure Python standard libraries.
        """
        # 1. Combine the entity and country for a highly targeted search
        search_term = f"{entity} {country}"
        query = urllib.parse.quote(search_term)
        
        # 2. Build the official Google News RSS URL
        # We keep hl=en-US to ensure the results are in English for the LLM to read easily
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        links = []
        try:
            # 3. Fetch the XML data (Spoofing a standard browser User-Agent to avoid 403 blocks)
            req = urllib.request.Request(
                rss_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
                
            # 4. Parse the XML feed natively
            root = ET.fromstring(xml_data)
            
            # 5. Extract the URLs safely
            for item in root.findall('./channel/item'):
                if len(links) >= max_results:
                    break
                    
                link_element = item.find('link')
                if link_element is not None and link_element.text:
                    links.append(link_element.text)
                    
        except Exception as e:
            logger.error(f"Failed to fetch articles for '{entity}' in '{country}': {e}")

        response = GetUrlContentResponse(links=links)
        return response