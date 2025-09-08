import os
import re
import json
from typing import Optional, Dict, List, Tuple, Set, Any
import spacy
from langdetect import detect, detect_langs, DetectorFactory, LangDetectException
from langdetect.language import Language
import openai
from openai import OpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Set seed for consistent language detection
DetectorFactory.seed = 0

# Initialize OpenAI client
def get_openai_client():
    """Initialize and return OpenAI client with the API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment")
        return None
    try:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None

# Global OpenAI client instance
openai_client = get_openai_client()

# Supported languages and their spaCy models
SUPPORTED_LANGUAGES = {
    'en': 'en_core_web_sm',  # English
    'hi': 'xx_ent_wiki_sm',   # Hindi (multilingual model)
    'kn': 'xx_ent_wiki_sm',   # Kannada (multilingual model)
}

# Disaster-related keywords in different languages
DISASTER_KEYWORDS = {
    'en': ['flood', 'earthquake', 'fire', 'storm', 'hurricane', 'cyclone', 'typhoon', 'tornado', 'landslide', 'tsunami', 'drought', 'wildfire'],
    'hi': ['बाढ़', 'भूकंप', 'आग', 'तूफान', 'चक्रवात', 'सुनामी', 'सूखा', 'जंगल की आग'],
    'kn': ['ಪ್ರವಾಹ', 'ಭೂಕಂಪ', 'ಬೆಂಕಿ', 'ಬಿರುಗಾಳಿ', 'ಚಂಡಮಾರುತ', 'ಸುನಾಮಿ', 'ಬರ', 'ಕಾಡ್ಗಿಚ್ಚು']
}

class NLPService:
    def __init__(self):
        self.nlp_models = {}
        self.openai_client = openai_client
        self._load_models()
        
        # Cache for storing processed results
        self.cache = {}
        
        # Default model configurations
        self.openai_config = {
            'model': "gpt-3.5-turbo",
            'temperature': 0.3,
            'max_tokens': 500,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
        }
        
    def _load_models(self):
        """Load spaCy models and initialize OpenAI client"""
        # Load the multilingual model for non-English languages
        try:
            # Try to load the multilingual model first
            self.nlp_models['xx'] = spacy.load('xx_ent_wiki_sm')
            logger.info("Loaded spaCy multilingual model")
        except OSError:
            logger.warning("spaCy multilingual model not found. Install with: python -m spacy download xx_ent_wiki_sm")
            self.nlp_models['xx'] = None
            
        # Load English model
        try:
            self.nlp_models['en'] = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp_models['en'] = spacy.blank('en')
            logger.info("Using blank English model")
        
        # Initialize OpenAI client
        self.openai_client = get_openai_client()
    
    def _rule_based_disaster_detection(self, text: str, language: str = "en") -> dict:
        """
        Rule-based disaster detection with severity assessment and sentiment analysis.
        Returns a dictionary with disaster type, severity, and sentiment.
        """
        text_lower = text.lower()
        
        # Severity indicators with weights
        severity_indicators = {
            'critical': ['critical', 'catastrophic', 'devastating', 'deadly', 'fatal', 'mass casualty', 'massive',
                        'large-scale', 'unprecedented', 'record-breaking', 'state of emergency', 'evacuation ordered'],
            'high': ['severe', 'extreme', 'major', 'dangerous', 'life-threatening', 'widespread', 'emergency',
                    'evacuation', 'warning issued', 'take shelter', 'immediate action'],
            'moderate': ['moderate', 'significant', 'substantial', 'considerable', 'advisory', 'be prepared',
                        'potential threat', 'developing situation'],
            'low': ['minor', 'small', 'localized', 'isolated', 'developing', 'watch', 'alert', 'caution',
                   'potential', 'possible']
        }
        
        # Sentiment indicators with weights
        sentiment_indicators = {
            'negative': {
                'high': ['kill', 'death', 'fatal', 'deadly', 'tragedy', 'catastrophe', 'devastation', 'disaster'],
                'medium': ['destroy', 'damage', 'injury', 'wound', 'trap', 'danger', 'hazard', 'toxic', 'emergency', 'crisis'],
                'low': ['evacuate', 'strand', 'block', 'warn', 'alert', 'threat']
            },
            'neutral': {
                'high': ['report', 'update', 'situation', 'condition', 'weather', 'event', 'incident', 'occur', 'happen'],
                'medium': ['affect', 'impact', 'develop', 'condition', 'level'],
                'low': ['area', 'region', 'location', 'time', 'date']
            },
            'positive': {
                'high': ['rescue', 'save', 'recover', 'help', 'aid', 'assist', 'support', 'donate', 'volunteer'],
                'medium': ['improve', 'better', 'stable', 'safe', 'secure'],
                'low': ['response', 'effort', 'team', 'support']
            }
        }
        
        # Define disaster keywords and their corresponding types with severity indicators
        disaster_keywords = {
            # Geological
            'earthquake': ['earthquake', 'tremor', 'seismic', 'richter scale', 'magnitude', 'epicenter', 'aftershock'],
            'volcanic_eruption': ['volcan', 'erupt', 'ash cloud', 'lava flow', 'pyroclastic'],
            'landslide': ['landslide', 'mudslide', 'rockslide', 'mudflow', 'debris flow', 'avalanche'],
            'sinkhole': ['sinkhole', 'ground collapse'],
            
            # Hydrological
            'flood': ['flood', 'inundat', 'submerged', 'water level', 'heavy rain', 'flash flood', 'river overflow'],
            'tsunami': ['tsunami', 'tidal wave', 'seismic sea wave'],
            'drought': ['drought', 'water shortage', 'water crisis', 'arid', 'scarcity of water'],
            
            # Meteorological
            'storm': ['storm', 'cyclone', 'hurricane', 'typhoon', 'tornado', 'thunderstorm', 'hailstorm', 'squall'],
            'heatwave': ['heatwave', 'heat wave', 'extreme heat', 'heatstroke', 'scorching'],
            'coldwave': ['coldwave', 'cold wave', 'extreme cold', 'blizzard', 'snowstorm', 'frost', 'freez'],
            
            # Climatological
            'wildfire': ['wildfire', 'bushfire', 'forest fire', 'brush fire', 'wildland fire'],
            'urban_fire': ['building fire', 'structure fire', 'house fire', 'industrial fire'],
            
            # Biological
            'pandemic': ['pandemic', 'epidemic', 'outbreak', 'virus', 'covid', 'influenza', 'ebola'],
            'insect_infestation': ['locust', 'grasshopper', 'pest infestation', 'insect swarm'],
            
            # Technological
            'industrial_accident': ['chemical spill', 'gas leak', 'nuclear', 'radiation', 'hazardous material'],
            'transport_accident': ['plane crash', 'train derail', 'shipwreck', 'car accident', 'pileup'],
            'infrastructure_failure': ['bridge collapse', 'dam break', 'power outage', 'blackout'],
            
            # Human-made
            'terrorism': ['terrorist', 'bombing', 'explosion', 'ied', 'suicide attack'],
            'civil_unrest': ['riot', 'protest', 'demonstration', 'civil unrest', 'clashes'],
            'war': ['war', 'armed conflict', 'airstrike', 'military operation', 'shelling']
        }
        
        # Check for severity indicators
        severity_indicators = {
            'major': ['major', 'severe', 'extreme', 'catastrophic', 'disastrous', 'devastating', 'deadly', 'fatal'],
            'minor': ['minor', 'small', 'light', 'brief', 'isolated']
        }
        
        # Initialize result with default values
        result = {
            'type': 'unknown',
            'severity': 'unknown',
            'sentiment': 'neutral',
            'confidence': 0.0
        }
        
        # Check for each disaster type
        matched_keywords = {}
        for disaster_type, keywords in disaster_keywords.items():
            matched = [k for k in keywords if k in text_lower]
            if matched:
                matched_keywords[disaster_type] = matched
        
        # If we found any matches, use the one with the most keywords matched
        if matched_keywords:
            # Sort by number of keywords matched (descending)
            sorted_matches = sorted(matched_keywords.items(), 
                                 key=lambda x: len(x[1]), 
                                 reverse=True)
            
            result['type'] = sorted_matches[0][0]
            result['confidence'] = min(1.0, len(sorted_matches[0][1]) * 0.2)  # Scale confidence
        
        # Determine severity
        for level, indicators in severity_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                result['severity'] = level
                break
        
        # Determine sentiment with weighted scoring
        sentiment_weights = {'high': 3, 'medium': 2, 'low': 1}
        sentiment_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for sentiment, levels in sentiment_indicators.items():
            for level, indicators in levels.items():
                weight = sentiment_weights[level]
                for indicator in indicators:
                    if indicator in text_lower:
                        sentiment_scores[sentiment] += weight
        
        # Get the sentiment with the highest score
        if all(score == 0 for score in sentiment_scores.values()):
            result['sentiment'] = 'neutral'  # Default to neutral if no indicators found
        else:
            result['sentiment'] = max(sentiment_scores.items(), key=lambda x: x[1])[0]
            
            # If negative indicators are present, they should have stronger weight
            if sentiment_scores['negative'] > 0 and result['sentiment'] != 'negative':
                # Only override if the difference isn't too large
                if sentiment_scores['negative'] >= sentiment_scores[result['sentiment']] * 0.7:
                    result['sentiment'] = 'negative'
        
        return result
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _detect_disaster_type_with_openai(self, text: str) -> str:
        """Detect disaster type using OpenAI's API with retry logic."""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
            
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a disaster detection assistant. Analyze the text and determine the type of disaster. Respond with only the disaster type (e.g., 'earthquake', 'flood', 'fire', 'hurricane', 'tornado', 'tsunami', 'volcano', 'drought', 'pandemic', 'unknown')."
                    },
                    {"role": "user", "content": f"Text: {text}\n\nDisaster type:"}
                ],
                max_tokens=20,
                temperature=0.1
            )
        )
        return response.choices[0].message.content.strip().lower()
    
    async def _detect_disaster_type(self, text: str, language: str = "en", use_openai: bool = True) -> dict:
        """
        Detect the type of disaster from the text with fallback to rule-based detection.
        Returns a dictionary containing:
        - type: The detected disaster type
        - severity: The assessed severity level
        - sentiment: The overall sentiment
        - confidence: Confidence score (0-1)
        """
        try:
            if use_openai and self.openai_client:
                # For OpenAI, we'll just get the type for now
                disaster_type = await self._detect_disaster_type_with_openai(text)
                return {
                    'type': disaster_type,
                    'severity': 'unknown',
                    'sentiment': 'neutral',
                    'confidence': 0.8  # Higher confidence for OpenAI
                }
            else:
                return self._rule_based_disaster_detection(text, language)
        except Exception as e:
            logger.warning(f"Error in disaster type detection: {e}")
            # Fall back to basic rule-based detection
            return self._rule_based_disaster_detection(text, language)
            
    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of the input text with confidence threshold"""
        if not text or len(text.strip()) < 3:
            return None
            
        try:
            # Clean text for better detection
            clean_text = re.sub(r'[^\w\s]', ' ', text[:1000])  # Limit to first 1000 chars
            
            # Get language with confidence scores
            languages = detect_langs(clean_text)
            if not languages:
                return None
                
            # Get the most probable language with sufficient confidence
            best_match = languages[0]
            if best_match.prob >= 0.5:  # Minimum confidence threshold
                return best_match.lang
                
            return None
            return language
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None
    
    def classify_disaster_type_rule_based(self, text: str) -> Optional[str]:
        """Rule-based disaster type classification using keywords"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        # Disaster type keywords
        disaster_keywords = {
            'earthquake': ['earthquake', 'quake', 'seismic', 'tremor', 'aftershock', 'magnitude', 'epicenter'],
            'flood': ['flood', 'flooding', 'inundation', 'overflow', 'water level', 'drainage', 'levee'],
            'fire': ['fire', 'wildfire', 'blaze', 'burning', 'smoke', 'flame', 'combustion', 'arson'],
            'storm': ['storm', 'hurricane', 'typhoon', 'cyclone', 'tornado', 'wind', 'gale', 'squall'],
            'drought': ['drought', 'dry', 'arid', 'water shortage', 'famine', 'crop failure'],
            'landslide': ['landslide', 'mudslide', 'avalanche', 'slope failure', 'rock fall'],
            'volcano': ['volcano', 'volcanic', 'eruption', 'lava', 'ash', 'magma', 'crater'],
            'tsunami': ['tsunami', 'tidal wave', 'seismic wave', 'coastal flooding'],
            'pandemic': ['pandemic', 'epidemic', 'virus', 'disease', 'outbreak', 'infection', 'covid'],
            'conflict': ['war', 'conflict', 'violence', 'attack', 'bombing', 'shooting', 'terrorism']
        }
        
        # Count keyword matches for each disaster type
        scores = {}
        for disaster_type, keywords in disaster_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[disaster_type] = score
        
        if not scores:
            return None
            
        # Return the disaster type with highest score
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def classify_disaster_type_llm(self, text: str) -> Optional[str]:
        """Use OpenAI to classify disaster type as fallback"""
        if not self.openai_client or not text:
            return None
            
        try:
            prompt = f"""
            Classify the following text as one of these disaster types: earthquake, flood, fire, storm, drought, landslide, volcano, tsunami, pandemic, conflict, or other.
            
            Text: "{text[:500]}"
            
            Respond with only the disaster type name, or "other" if none apply.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            valid_types = ['earthquake', 'flood', 'fire', 'storm', 'drought', 'landslide', 'volcano', 'tsunami', 'pandemic', 'conflict', 'other']
            if result in valid_types:
                return result if result != 'other' else None
            else:
                return None
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return None
    
    def classify_disaster_type(self, text: str) -> Optional[str]:
        """Classify disaster type using rule-based approach with LLM fallback"""
        if not text:
            return None
            
        # Try rule-based classification first
        rule_result = self.classify_disaster_type_rule_based(text)
        if rule_result:
            return rule_result
            
        # Fallback to LLM if rule-based fails
        return self.classify_disaster_type_llm(text)
    
    def extract_locations_ner(self, text: str) -> List[Dict[str, any]]:
        """Extract locations using spaCy NER"""
        if not self.nlp or not text:
            return []
            
        try:
            doc = self.nlp(text)
            locations = []
            
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC', 'FAC']:  # Geopolitical entity, Location, Facility
                    locations.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'confidence': 0.8,  # spaCy doesn't provide confidence scores by default
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            return locations
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return []
    
    def extract_locations_llm(self, text: str) -> List[Dict[str, any]]:
        """Use OpenAI to extract locations as fallback"""
        if not self.openai_client or not text:
            return []
            
        try:
            prompt = f"""
            Extract all location names (cities, countries, regions, states, provinces) from the following text.
            Return them as a JSON array of objects with "text" and "type" fields.
            
            Text: "{text[:1000]}"
            
            Example format: [{{"text": "California", "type": "state"}}, {{"text": "Los Angeles", "type": "city"}}]
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            locations = json.loads(result)
            
            # Add confidence score
            for loc in locations:
                loc['confidence'] = 0.7
                loc['start'] = 0  # LLM doesn't provide position info
                loc['end'] = 0
            
            return locations
            
        except Exception as e:
            logger.error(f"LLM location extraction failed: {e}")
            return []
    
    def extract_locations(self, text: str) -> List[Dict[str, any]]:
        """Extract locations using NER with LLM fallback"""
        if not text:
            return []
            
        # Try NER first
        ner_locations = self.extract_locations_ner(text)
        if ner_locations:
            return ner_locations
            
        # Fallback to LLM if NER fails or returns no results
        return self.extract_locations_llm(text)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_openai(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """Helper method to call OpenAI API with retry logic"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        config = self.openai_config.copy()
        config.update(kwargs)
        
        try:
            response = await self.openai_client.chat.completions.create(
                messages=messages,
                **config
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of the text using OpenAI"""
        if not text:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            
        cache_key = f"sentiment_{hash(text)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        prompt = f"""Analyze the sentiment of the following text and return a JSON object with 'positive', 'negative', and 'neutral' scores between 0 and 1 that add up to 1.0.
        
        Text: ""{text}""
        
        Return only the JSON object, nothing else."""
        
        try:
            result = await self._call_openai(
                prompt=prompt,
                temperature=0.1,
                max_tokens=100
            )
            sentiment = json.loads(result)
            self.cache[cache_key] = sentiment
            return sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of the text using OpenAI"""
        if not text:
            return ""
            
        cache_key = f"summary_{hash(text)}_{max_length}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        prompt = f"""Please provide a concise summary of the following text in {max_length//2} words or less. Focus on the key points and main ideas.
        
        Text: ""{text}""
        
        Summary:"""
        
        try:
            summary = await self._call_openai(
                prompt=prompt,
                max_tokens=max_length,
                temperature=0.3
            )
            self.cache[cache_key] = summary.strip()
            return summary.strip()
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return text[:max_length] + ("..." if len(text) > max_length else "")

    async def extract_key_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract key entities from the text using OpenAI"""
        if not text:
            return []
            
        cache_key = f"entities_{hash(text)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        prompt = f"""Extract the key entities (people, organizations, locations, dates, and important terms) from the following text. 
        Return a JSON array of objects, each with 'text' (the entity text) and 'type' (the entity type).
        
        Text: ""{text}""
        
        Return only the JSON array, nothing else."""
        
        try:
            result = await self._call_openai(
                prompt=prompt,
                temperature=0.1,
                max_tokens=500
            )
            entities = json.loads(result)
            self.cache[cache_key] = entities
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def process_text(self, text: str) -> Dict:
        """Process text to extract disaster information with language support and OpenAI enhancements"""
        if not text:
            return {
                "language": None, 
                "disaster_type": None, 
                "locations": [],
                "sentiment": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "summary": "",
                "key_entities": []
            }
            
        # Detect language
        language = self.detect_language(text) or "en"
        
        # Get appropriate NLP model (fallback to multilingual if specific language not available)
        nlp = self.nlp_models.get(language) or self.nlp_models.get('xx') or self.nlp_models.get('en')
        
        # Initialize base result
        result = {
            "language": language,
            "disaster_type": None,
            "locations": [],
            "sentiment": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
            "summary": "",
            "key_entities": []
        }
        
        try:
            # Basic processing with spaCy if available
            if nlp:
                doc = nlp(text)
                
                # Extract and categorize entities
                entities = []
                location_entities = []
                location_phrases = set()
                
                # First pass: Extract all entities
                for ent in doc.ents:
                    entity = {
                        "text": ent.text,
                        "label": ent.label_,
                        "type": ent.label_.lower(),
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "source": "ner"
                    }
                    
                    # Categorize entities
                    if ent.label_ in ("GPE", "LOC", "FAC", "NORP"):
                        entity["category"] = "location"
                        location_entities.append(entity)
                        location_phrases.add(ent.text.lower())
                    elif ent.label_ == "ORG":
                        entity["category"] = "organization"
                        entities.append(entity)
                    elif ent.label_ == "PERSON":
                        entity["category"] = "person"
                        entities.append(entity)
                    elif ent.label_ in ("DATE", "TIME"):
                        entity["category"] = "time"
                        entities.append(entity)
                    elif ent.label_ in ("MONEY", "QUANTITY", "CARDINAL", "PERCENT"):
                        entity["category"] = "quantity"
                        entities.append(entity)
                    else:
                        entity["category"] = "other"
                        entities.append(entity)
                
                # Second pass: Look for location patterns that NER might have missed
                location_patterns = [
                    ("NEAR", ["near", "close to", "in the area of"]),
                    ("IN", ["in", "at", "inside", "within"]),
                    ("OF", ["of", "from"]),
                    ("CITY_REGION", ["city", "town", "village", "county", "district", "prefecture"]),
                    ("REGION", ["region", "area", "zone", "territory"]),
                    ("COUNTRY", ["country", "nation", "state", "province"])
                ]
                
                # Look for location phrases using patterns
                for i, token in enumerate(doc):
                    # Skip if already part of a location entity
                    if any(ent.start_char <= token.idx < ent.end_char for ent in doc.ents):
                        continue
                        
                    # Check for location patterns
                    for pattern_type, patterns in location_patterns:
                        if token.text.lower() in patterns:
                            # Look for nearby location words
                            window = 3  # Number of words to check after the pattern
                            for j in range(1, min(window + 1, len(doc) - i)):
                                next_token = doc[i + j]
                                # Skip if next token is a stop word or punctuation
                                if next_token.is_stop or next_token.is_punct:
                                    continue
                                    
                                # Check if this looks like a location (proper noun, capitalized, etc.)
                                if (next_token.pos_ in ("PROPN", "NOUN") and 
                                    next_token.text[0].isupper() and 
                                    next_token.text.lower() not in location_phrases):
                                    
                                    location_text = f"{token.text} {next_token.text}"
                                    location_entities.append({
                                        "text": location_text,
                                        "label": "LOC",
                                        "type": "location",
                                        "category": "location",
                                        "start_char": token.idx,
                                        "end_char": next_token.idx + len(next_token.text),
                                        "source": "pattern",
                                        "pattern": pattern_type
                                    })
                                    location_phrases.add(location_text.lower())
                                    break
                
                # Extract numerical values and measurements
                for token in doc:
                    if token.like_num or token.is_digit:
                        # Check if it's part of a measurement
                        if token.i < len(doc) - 1 and doc[token.i + 1].is_alpha and len(doc[token.i + 1]) <= 3:
                            entities.append({
                                "text": f"{token.text} {doc[token.i + 1].text}",
                                "label": "MEASUREMENT",
                                "type": "measurement",
                                "category": "quantity"
                            })
                    
                    # Extract hashtags and mentions
                    if token.text.startswith('@'):
                        entities.append({
                            "text": token.text,
                            "label": "MENTION",
                            "type": "social",
                            "category": "social_media"
                        })
                    elif token.text.startswith('#'):
                        entities.append({
                            "text": token.text,
                            "label": "HASHTAG",
                            "type": "social",
                            "category": "social_media"
                        })
                
                # Add locations to entities and store separately
                result["locations"] = location_entities
                result["entities"] = entities + location_entities
                
                # Enhanced disaster type detection with severity and sentiment
                disaster_info = await self._detect_disaster_type(doc.text, language)
                result.update({
                    "disaster_type": disaster_info['type'],
                    "disaster_severity": disaster_info['severity'],
                    "disaster_confidence": disaster_info['confidence']
                })
                
                # Update overall sentiment if not already set by OpenAI
                if result["sentiment"]["neutral"] == 1.0:  # Default neutral sentiment
                    sentiment = disaster_info['sentiment']
                    result["sentiment"] = {
                        'positive': 1.0 if sentiment == 'positive' else 0.0,
                        'negative': 1.0 if sentiment == 'negative' else 0.0,
                        'neutral': 1.0 if sentiment == 'neutral' else 0.0
                    }
            
            # Enhanced processing with OpenAI if available
            if self.openai_client:
                # Run all OpenAI tasks in parallel
                sentiment_task = self.analyze_sentiment(text)
                summary_task = self.summarize_text(text)
                entities_task = self.extract_key_entities(text)
                
                # Wait for all tasks to complete
                sentiment, summary, key_entities = await asyncio.gather(
                    sentiment_task, summary_task, entities_task
                )
                
                result.update({
                    "sentiment": sentiment,
                    "summary": summary,
                    "key_entities": key_entities
                })
                
                # If we didn't get a disaster type from spaCy, try to get it from OpenAI
                if not result["disaster_type"] and key_entities:
                    for entity in key_entities:
                        if entity.get("type", "").lower() in ["disaster", "event"]:
                            result["disaster_type"] = entity.get("text")
                            break
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing text in language {language}: {e}")
            return result

# Global instance
nlp_service = NLPService()
