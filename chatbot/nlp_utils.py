import spacy
import logging
from django.utils import timezone
import re

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def detect_product_queries(message):
    product_keywords = [
        'product', 'item', 'inventory', 'stock', 'price', 'cost',
        'buy', 'purchase', 'order', 'available', 'sell', 'selling',
        'menu', 'catalog', 'offer', 'special', 'deal'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in product_keywords)

def detect_business_queries(message):
    business_keywords = [
        'business', 'company', 'store', 'shop', 'restaurant',
        'service', 'provider', 'location', 'address', 'contact',
        'phone', 'email', 'website', 'hours', 'open', 'close',
        'owner', 'about', 'description', 'verify', 'verified'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in business_keywords)

def extract_intent_and_entities(message):
    message_lower = message.lower().strip()
    doc = nlp(message_lower)

    entities = {
        "cities": [],
        "business_names": [],
        "categories": [],
        "product_names": []
    }

    if len(message.split()) <= 3:
        logger.info(f"Treating short message as business name search: {message}")
        entities["business_names"] = [message]
        return "find", entities

    intents = {
        "find": ["find", "show", "search", "look for", "where can i find",
                 "need", "looking for", "list", "get", "businesses"],
        "contact": ["phone", "contact", "call", "number", "how to reach",
                    "what's the number for", "reach"],
        "location": ["where is", "location of", "address of", "located",
                     "address for", "find address"],
        "add_business": ["add", "submit", "register", "new business",
                         "how to add", "business registration", "join directory"],
        "categories": ["category", "categories", "types", "business types",
                       "what kinds", "list categories"],
        "greeting": ["hello", "hi", "hey", "greetings", "good morning",
                     "good afternoon", "good evening"],
        "thanks": ["thank", "thanks", "appreciate", "thank you",
                   "thanks a lot", "many thanks"],
        "help": ["help", "what can you do", "support", "assistance",
                 "how to use", "guide me"],
        "list_all": ["all businesses", "list all businesses",
                     "show all businesses", "complete list"],
        "find_posts": ["posts about", "announcements for", "offers for",
                       "services for", "products for", "looking for posts"]
    }

    detected_intent = None
    for intent, keywords in intents.items():
        if any(re.search(rf'\b{re.escape(keyword)}\b', message_lower) for keyword in keywords):
            detected_intent = intent
            break

    if not detected_intent and ("where is" in message_lower or "location of" in message_lower):
        detected_intent = "location"
        parts = re.split(r'where is|location of', message_lower, flags=re.IGNORECASE)
        if len(parts) > 1:
            business_name = parts[1].strip()
            entities["business_names"].append(business_name)

    common_categories = [
        "restaurant", "cafe", "school", "hotel", "shop", "store",
        "hospital", "clinic", "bank", "supermarket", "salon", "pharmacy",
        "lawyer", "doctor", "contractor", "plumber", "electrician", "gym",
        "spa", "car repair", "printing", "fashion", "construction",
        "consultancy", "education", "training", "real estate", "transportation",
        "logistics", "manufacturing", "security", "tourism", "mobile money",
        "supplies", "electronics", "furniture", "food", "beverage"
    ]

    for ent in doc.ents:
        if ent.label_ == "GPE":
            entities["cities"].append(ent.text)
        elif ent.label_ in ("ORG", "PRODUCT", "FAC"):
            entities["business_names"].append(ent.text)

    for token in doc:
        if token.text.lower() in common_categories and token.text.lower() not in entities["categories"]:
            entities["categories"].append(token.text.lower())

    if "businesses in" in message_lower and not detected_intent:
        detected_intent = "find"
        parts = message_lower.split("businesses in")
        if len(parts) > 1:
            city_part = parts[1].strip()
            entities["cities"].append(city_part)

    if "posts about" in message_lower and not detected_intent:
        detected_intent = "find_posts"
        parts = message_lower.split("posts about")
        if len(parts) > 1:
            topic = parts[1].strip()
            if topic in common_categories:
                entities["categories"].append(topic)
            else:
                entities["business_names"].append(topic)

    if not detected_intent and detect_product_queries(message_lower):
        detected_intent = "product_query"
        if "price of" in message_lower:
            parts = message_lower.split("price of")
            if len(parts) > 1:
                entities["product_names"].append(parts[1].strip())
        elif "cost of" in message_lower:
            parts = message_lower.split("cost of")
            if len(parts) > 1:
                entities["product_names"].append(parts[1].strip())

    if not detected_intent and detect_business_queries(message_lower):
        if "about" in message_lower and ("business" in message_lower or "company" in message_lower):
            detected_intent = "business_details"
            parts = message_lower.split("about")
            if len(parts) > 1:
                entities["business_names"] = [parts[1].replace("business", "").replace("company", "").strip()]

    for key in entities:
        entities[key] = list(set([e for e in entities[key] if e.strip()]))

    if not detected_intent:
        if entities["business_names"] or entities["cities"] or entities["categories"]:
            detected_intent = "find"
        else:
            detected_intent = "help"

    return detected_intent, entities
