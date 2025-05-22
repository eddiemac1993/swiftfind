from django.shortcuts import render
from django.http import JsonResponse
import json
import logging
from .nlp_utils import extract_intent_and_entities
from .utils import (
    get_businesses_by_criteria,
    get_business_contact,
    get_all_categories,
    get_business_details,
    get_all_businesses,
    get_matching_posts,
    format_business_result
)

logger = logging.getLogger(__name__)

def chat(request):
    if request.method == 'GET':
        return render(request, 'chat.html')
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({'response': "Please type a message.", 'is_html': False})
            
            intent, entities = extract_intent_and_entities(message)
            logger.info(f"Detected intent: {intent}, entities: {entities} for message: {message}")
            
            # Handle different intents
            if intent == "greeting":
                return JsonResponse({
                    'response': "Hello! How can I help you with the business directory today?",
                    'is_html': False
                })
            
            elif intent == "thanks":
                return JsonResponse({
                    'response': "You're welcome! Is there anything else I can help you with?",
                    'is_html': False
                })
            
            elif intent == "help":
                help_text = """
                I can help you with:<br><br>
                <strong>Finding businesses</strong><br>
                - "Find restaurants in New York"<br>
                - "Show me hardware stores"<br>
                - "List all businesses"<br>
                - "Businesses in Lusaka"<br>
                - Just type a business name like "E-trac"<br><br>
                <strong>Finding posts</strong><br>
                - "Posts about plumbing services"<br>
                - "Show me recent announcements"<br>
                - "Find special offers"<br><br>
                <strong>Contact information</strong><br>
                - "What's the phone number for ABC Corp?"<br>
                - "How to contact XYZ Services?"<br>
                - "Where is Ditso located?"<br><br>
                <strong>Categories</strong><br>
                - "What business categories do you have?"<br>
                - "List all categories"<br><br>
                <strong>Adding businesses</strong><br>
                - "How to add my business?"<br>
                - "Register new business"
                """
                return JsonResponse({
                    'response': help_text,
                    'is_html': True
                })
            
            elif intent == "find" or intent == "find_posts":
                city = entities["cities"][0] if entities["cities"] else None
                category = entities["categories"][0] if entities["categories"] else None
                query = " ".join(entities["business_names"]) if entities["business_names"] else None
                
                # Special handling for "businesses in [city]" pattern
                if not city and "businesses in" in message.lower():
                    parts = message.lower().split("businesses in")
                    if len(parts) > 1:
                        city = parts[1].strip()
                
                # If no query but we have a message, use the whole message
                if not query and message:
                    query = message
                
                businesses = get_businesses_by_criteria(
                    query=query,
                    city=city,
                    category_name=category
                )
                
                if businesses:
                    # Prioritize exact matches and businesses in the requested city
                    exact_matches = [b for b in businesses 
                                   if (b.name.lower() == message.lower()) or 
                                   (city and city.lower() in b.city.lower() if b.city else False)]
                    
                    other_matches = [b for b in businesses if b not in exact_matches]
                    
                    response = "<strong>Here are some businesses I found:</strong><br><br>"
                    
                    # Show exact matches first
                    for biz in exact_matches:
                        response += format_business_result(biz, query)
                    
                    # Then show other matches
                    for biz in other_matches:
                        response += format_business_result(biz, query)
                    
                    return JsonResponse({
                        'response': response,
                        'is_html': True
                    })
                else:
                    no_results_msg = "I couldn't find any matching businesses."
                    if city:
                        no_results_msg += f" in {city}"
                    if category:
                        no_results_msg += f" in the {category} category"
                    if query:
                        no_results_msg += f" for '{query}'"
                    no_results_msg += ". Try being more specific or check your spelling."
                    
                    return JsonResponse({
                        'response': no_results_msg,
                        'is_html': False
                    })
            
            elif intent == "list_all":
                businesses = get_all_businesses()
                if businesses:
                    response = "<strong>Here are some businesses in our directory:</strong><br><br>"
                    for biz in businesses:
                        response += format_business_result(biz)
                    return JsonResponse({
                        'response': response,
                        'is_html': True
                    })
                else:
                    return JsonResponse({
                        'response': "I couldn't find any businesses in the directory.",
                        'is_html': False
                    })
            
            elif intent == "contact":
                if entities["business_names"]:
                    business_name = entities["business_names"][0]
                    contact_info = get_business_contact(business_name)
                    if contact_info:
                        response = f"<strong>Contact information for {business_name}:</strong><br>"
                        if contact_info['phone']:
                            response += f"📞 Phone: {contact_info['phone']}<br>"
                        if contact_info['email']:
                            response += f"✉️ Email: {contact_info['email']}<br>"
                        if contact_info['website']:
                            response += f"🌐 Website: <a href='{contact_info['website']}' target='_blank'>{contact_info['website']}</a><br>"
                        if contact_info['address']:
                            response += f"📍 Address: {contact_info['address']}"
                            if contact_info['city']:
                                response += f", {contact_info['city']}"
                        return JsonResponse({
                            'response': response,
                            'is_html': True
                        })
                    return JsonResponse({
                        'response': f"Sorry, I couldn't find contact information for {business_name}",
                        'is_html': False
                    })
                return JsonResponse({
                    'response': "Please specify which business you want contact information for.",
                    'is_html': False
                })
            
            elif intent == "categories":
                categories = get_all_categories()
                return JsonResponse({
                    'response': "<strong>Available categories:</strong><br>- " + "<br>- ".join(categories),
                    'is_html': True
                })
            
            elif intent == "add_business":
                return JsonResponse({
                    'response': "To add a business, please visit our website and fill out the business registration form. Would you like me to provide the link?",
                    'is_html': False
                })
            
            else:
                # If we don't understand the intent but the message is short, try treating it as a business name
                if len(message.split()) <= 4:
                    businesses = get_businesses_by_criteria(query=message)
                    if businesses:
                        response = "<strong>Here are some businesses I found:</strong><br><br>"
                        for biz in businesses:
                            response += format_business_result(biz, message)
                        return JsonResponse({
                            'response': response,
                            'is_html': True
                        })
                
                return JsonResponse({
                    'response': "I'm not sure I understand. You can ask me to:<br>- Find businesses<br>- Find posts/announcements<br>- Get contact information<br>- List categories<br>- Or ask about adding a business<br><br>Type 'help' to see what I can do.",
                    'is_html': True
                })
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return JsonResponse({
                'error': f"An error occurred: {str(e)}",
                'is_html': False
            }, status=500)
    
    return JsonResponse({
        'error': "Invalid request method",
        'is_html': False
    }, status=400)