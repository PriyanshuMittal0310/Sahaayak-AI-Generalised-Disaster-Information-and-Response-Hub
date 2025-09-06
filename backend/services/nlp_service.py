import os
import re
from typing import Optional, Dict, List, Tuple
import spacy
from langdetect import detect, DetectorFactory
import openai
from loguru import logger

# Set seed for consistent language detection
DetectorFactory.seed = 0

class NLPService:
    def __init__(self):
        self.nlp = None
        self.openai_client = None
        self._load_models()
        
    def _load_models(self):
        """Load spaCy model and initialize OpenAI client"""
        try:
            # Try to load the English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            # Fallback to basic model
            try:
                self.nlp = spacy.blank("en")
                logger.info("Using spaCy blank English model")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                self.nlp = None
        
        # Initialize OpenAI client if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OPENAI_API_KEY not found. LLM fallback disabled")
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of the input text"""
        if not text or len(text.strip()) < 3:
            return None
            
        try:
            # Clean text for better detection
            clean_text = re.sub(r'[^\w\s]', ' ', text[:1000])  # Limit to first 1000 chars
            language = detect(clean_text)
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
    
    def process_text(self, text: str) -> Dict[str, any]:
        """Process text to extract language, disaster type, and locations"""
        if not text:
            return {
                'language': None,
                'disaster_type': None,
                'locations': []
            }
            
        language = self.detect_language(text)
        disaster_type = self.classify_disaster_type(text)
        locations = self.extract_locations(text)
        
        return {
            'language': language,
            'disaster_type': disaster_type,
            'locations': locations
        }

# Global instance
nlp_service = NLPService()
