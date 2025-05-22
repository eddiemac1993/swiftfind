import spacy
import logging

logger = logging.getLogger(__name__)

try:
    # Load the small English model
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def extract_intent_and_entities(message):
    message_lower = message.lower().strip()
    doc = nlp(message_lower)

    # If message is short (1-3 words), assume it's a business name search
    if len(message.split()) <= 3:
        logger.info(f"Treating short message as business name search: {message}")
        return "find", {"business_names": [message], "cities": [], "categories": []}

    intents = {
        "find": ["find", "show", "search", "look for", "where can i find", "need", "looking for", "list", "get"],
        "contact": ["phone", "contact", "call", "number", "how to reach", "what's the number for", "where is"],
        "add_business": ["add", "submit", "register", "new business"],
        "categories": ["category", "categories", "types", "business types", "what kinds"],
        "greeting": ["hello", "hi", "hey", "greetings"],
        "thanks": ["thank", "thanks", "appreciate"],
        "help": ["help", "what can you do", "support"],
        "list_all": ["all businesses", "list all businesses", "show all businesses"],
        "find_posts": ["posts about", "announcements for", "offers for", "services for", "products for"]
    }

    # Detect intent
    detected_intent = None
    for intent, keywords in intents.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_intent = intent
            break

    # Handle post-specific searches
    if not detected_intent:
        for post_type in ["posts", "announcements", "offers", "services", "products"]:
            if post_type in message_lower:
                detected_intent = "find_posts"
                break

    # Extract entities with improved logic
    entities = {
        "cities": [],
        "business_names": [],
        "categories": []
    }
    
    # Common business categories to look for
    common_categories = [
        "restaurant", "cafe", "school", "hotel", "shop", 
        "store", "hospital", "clinic", "bank", "supermarket",
        "salon", "pharmacy", "lawyer", "doctor", "contractor",
        "plumber", "electrician", "gym", "spa", "car repair",
        "printing", "fashion", "construction", "consultancy",
        "education", "training", "real estate", "transportation",
        "logistics", "manufacturing", "security"
    ]
    
    # Extract cities and business names
    for ent in doc.ents:
        if ent.label_ == "GPE":  # Geographical locations
            entities["cities"].append(ent.text)
        elif ent.label_ in ("ORG", "PRODUCT", "FAC"):  # Organizations/business names/facilities
            entities["business_names"].append(ent.text)
    
    # Extract categories from message
    for token in doc:
        if token.text.lower() in common_categories and token.text.lower() not in entities["categories"]:
            entities["categories"].append(token.text.lower())
    
    # If no explicit category but intent is find, look for implied categories
    if (detected_intent == "find" or detected_intent == "find_posts") and not entities["categories"]:
        for cat in common_categories:
            if cat in message_lower and cat not in entities["categories"]:
                entities["categories"].append(cat)
                break
    
    # Handle "where is" questions
    if "where is" in message_lower and not detected_intent:
        detected_intent = "contact"
        if not entities["business_names"]:
            # Try to extract business name from the rest of the message
            remaining_text = message_lower.split("where is")[1].strip()
            entities["business_names"].append(remaining_text)
    
    # Handle "businesses in [city]" pattern
    if "businesses in" in message_lower and not detected_intent:
        detected_intent = "find"
        parts = message_lower.split("businesses in")
        if len(parts) > 1:
            city_part = parts[1].strip()
            entities["cities"].append(city_part)
    
    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    # If no intent detected but we have entities, assume it's a find intent
    if not detected_intent and (entities["business_names"] or entities["cities"] or entities["categories"]):
        detected_intent = "find"
    
    return detected_intent, entities