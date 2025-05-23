from django.shortcuts import render
from django.http import JsonResponse
import json
import logging
from .models import UserQuery
from .nlp_utils import extract_intent_and_entities
from .utils import (
    get_businesses_by_criteria,
    get_business_contact,
    get_all_categories,
    get_business_details,
    get_all_businesses,
    format_business_result
)
from django.utils.html import escape

logger = logging.getLogger(__name__)

def get_help_response():
    return """
    <strong>I can help you with:</strong><br><br>
    <strong>🔍 Finding businesses</strong><br>
    - <a href="#" class="suggestion">Find restaurants in New York</a><br>
    - <a href="#" class="suggestion">Show me hardware stores</a><br>
    - <a href="#" class="suggestion">List all businesses</a><br>
    - <a href="#" class="suggestion">Businesses in Lusaka</a><br>
    - Just type a business name like "E-trac"<br><br>
    <strong>📢 Finding posts</strong><br>
    - <a href="#" class="suggestion">Posts about plumbing services</a><br>
    - <a href="#" class="suggestion">Show me recent announcements</a><br>
    - <a href="#" class="suggestion">Find special offers</a><br><br>
    <strong>📞 Contact information</strong><br>
    - <a href="#" class="suggestion">What's the phone number for ABC Corp?</a><br>
    - <a href="#" class="suggestion">How to contact XYZ Services?</a><br>
    - <a href="#" class="suggestion">Where is Ditso located?</a><br><br>
    <strong>📂 Categories</strong><br>
    - <a href="#" class="suggestion">What business categories do you have?</a><br>
    - <a href="#" class="suggestion">List all categories</a><br><br>
    <strong>➕ Adding businesses</strong><br>
    - <a href="#" class="suggestion">How to add my business?</a><br>
    - <a href="#" class="suggestion">Register new business</a>
    """

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
            logger.info(f"Detected intent: {intent}, entities: {entities}")
            
            # Save user query for analytics
            UserQuery.objects.create(
                query=message,
                intent=intent,
                entities=str(entities),
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR'),
                session_key=request.session.session_key or None
            )
            
            # Intent handling
            if intent == "greeting":
                response = "Hello! How can I help you with the business directory today?"
                is_html = False
            
            elif intent == "thanks":
                response = "You're welcome! Is there anything else I can help you with?"
                is_html = False
            
            elif intent == "help":
                response = get_help_response()
                is_html = True
            
            elif intent in ["find", "find_posts"]:
                city = entities["cities"][0] if entities["cities"] else None
                category = entities["categories"][0] if entities["categories"] else None
                query = " ".join(entities["business_names"]) if entities["business_names"] else None
                
                if not query and message:
                    query = message
                
                businesses = get_businesses_by_criteria(
                    query=query,
                    city=city,
                    category_name=category
                )
                
                if businesses:
                    response = "<strong>Here are some businesses I found:</strong><br><br>"
                    for biz in businesses:
                        response += format_business_result(biz, query)
                    is_html = True
                else:
                    response = f"I couldn't find any matching businesses"
                    if city:
                        response += f" in {city}"
                    if category:
                        response += f" in the {category} category"
                    if query:
                        response += f" for '{query}'"
                    response += ". Try being more specific or check your spelling."
                    is_html = False
            
            elif intent == "list_all":
                businesses = get_all_businesses()
                if businesses:
                    response = "<strong>Here are some businesses in our directory:</strong><br><br>"
                    for biz in businesses:
                        response += format_business_result(biz)
                    is_html = True
                else:
                    response = "I couldn't find any businesses in the directory."
                    is_html = False
            
            elif intent == "location":
                if entities["business_names"]:
                    business_name = entities["business_names"][0]
                    business = get_business_details(business_name)
                    if business:
                        response = f"<strong>{escape(business.name)}</strong> is located at:<br>"
                        if business.address:
                            response += f"📍 {escape(business.address)}"
                            if business.city:
                                response += f", {escape(business.city)}"
                        else:
                            response += "Sorry, I don't have the exact address, but it's in "
                            response += escape(business.city) if business.city else "an unknown location"
                        is_html = True
                    else:
                        response = f"I couldn't find information about {escape(business_name)}. Please check the name and try again."
                        is_html = False
                else:
                    response = "Please specify which business you're asking about."
                    is_html = False
            
            elif intent == "contact":
                if entities["business_names"]:
                    business_name = entities["business_names"][0]
                    contact_info = get_business_contact(business_name)
                    if contact_info:
                        response = f"<strong>Contact information for {escape(contact_info['name'])}:</strong><br>"
                        if contact_info['phone']:
                            response += f"📞 <a href='tel:{contact_info['phone']}'>{escape(contact_info['phone'])}</a><br>"
                        if contact_info['email']:
                            response += f"✉️ <a href='mailto:{contact_info['email']}'>{escape(contact_info['email'])}</a><br>"
                        if contact_info['website']:
                            website_display = escape(contact_info['website'].replace('http://', '').replace('https://', ''))
                            response += f"🌐 <a href='{contact_info['website']}' target='_blank'>{website_display}</a><br>"
                        if contact_info['address']:
                            response += f"📍 {escape(contact_info['address'])}"
                            if contact_info['city']:
                                response += f", {escape(contact_info['city'])}"
                        is_html = True
                    else:
                        response = f"Sorry, I couldn't find contact information for {escape(business_name)}"
                        is_html = False
                else:
                    response = "Please specify which business you want contact information for."
                    is_html = False
            
            elif intent == "categories":
                categories = get_all_categories()
                response = "<strong>Available categories:</strong><br>- " + "<br>- ".join(escape(c) for c in categories)
                is_html = True
            
            elif intent == "add_business":
                response = """
                <strong>To add your business to our directory:</strong><br><br>
                1. Visit our business registration page at <a href="/business/register/" target="_blank">/business/register/</a><br>
                2. Fill out the form with your business details<br>
                3. Submit for approval<br><br>
                Would you like me to guide you through the registration process?
                """
                is_html = True
            
            else:
                # Fallback for unrecognized queries
                if len(message.split()) <= 4:
                    businesses = get_businesses_by_criteria(query=message)
                    if businesses:
                        response = "<strong>Here are some businesses I found:</strong><br><br>"
                        for biz in businesses:
                            response += format_business_result(biz, message)
                        is_html = True
                    else:
                        response = get_help_response()
                        is_html = True
                else:
                    response = get_help_response()
                    is_html = True
            
            return JsonResponse({
                'response': response,
                'is_html': is_html
            })
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return JsonResponse({
                'error': "Sorry, I encountered an error processing your request. Please try again.",
                'is_html': False
            }, status=500)
    
    return JsonResponse({
        'error': "Invalid request method",
        'is_html': False
    }, status=400)