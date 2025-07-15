import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape
from .models import UserQuery
from .nlp_utils import extract_intent_and_entities
from .utils import (
    get_businesses_by_criteria,
    get_business_contact,
    get_all_categories,
    get_business_details,
    get_all_businesses,
    format_business_result,
    get_business_products,
    format_product_response,
    get_business_full_details
)
from datetime import datetime
import random
import urllib.parse
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

            # Get current hour for time-based greetings
            current_hour = datetime.now().hour
            greeting = "Good morning" if 5 <= current_hour < 12 else "Good afternoon" if 12 <= current_hour < 17 else "Good evening"

            # Intent handling
            if intent == "greeting":
                username = request.user.username if request.user.is_authenticated else "there"
                responses = [
                    f"{greeting}, {username}! How can I assist you with our business directory today?",
                    f"{greeting}! What can I help you find in our business directory?",
                    f"{greeting}! Looking for a specific business or service today?"
                ]
                response = random.choice(responses)
                is_html = False

            elif intent == "thanks":
                responses = [
                    "You're welcome! Is there anything else I can help you with?",
                    "Happy to help! Let me know if you need anything else.",
                    "My pleasure! What else can I assist you with today?"
                ]
                response = random.choice(responses)
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
                    response = f"<strong>Here are some businesses that match your request"
                    if query:
                        response += f" for '{escape(query)}'"
                    if city:
                        response += f" in {escape(city)}"
                    if category:
                        response += f" (category: {escape(category)})"
                    response += ":</strong><br><br>"

                    for biz in businesses:
                        response += format_business_result(biz, query)

                    # Add follow-up suggestion
                    if len(businesses) == 1:
                        biz = businesses[0]
                        response += f"<br>Would you like more details about {escape(biz.name)}, their contact information, or products?"
                    is_html = True
                else:
                    response = f"I couldn't find any matching businesses"
                    if city:
                        response += f" in {escape(city)}"
                    if category:
                        response += f" in the {escape(category)} category"
                    if query:
                        response += f" for '{escape(query)}'"

                    # Provide helpful suggestions
                    response += ".<br><br>Try these tips:<br>"
                    response += "- Check your spelling<br>"
                    response += "- Try a broader search (e.g., 'restaurants' instead of 'Italian restaurants')<br>"
                    response += "- Or ask me for help with <a href='#' class='suggestion' onclick='sendSuggestion(\"Help me find businesses\")'>finding businesses</a>"
                    is_html = True

            elif intent == "list_all":
                businesses = get_all_businesses()
                if businesses:
                    response = "<strong>Here are some businesses in our directory:</strong><br><br>"
                    for biz in businesses:
                        response += format_business_result(biz)
                    response += "<br>You can refine your search by adding a location or category, like 'restaurants in Lusaka'."
                    is_html = True
                else:
                    response = "Our directory is currently empty. Would you like to <a href='/business/register/'>register your business</a>?"
                    is_html = True

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

                            # Add map link if address exists
                            map_query = urllib.parse.quote(f"{business.address}, {business.city}" if business.city else business.address)
                            response += f"<br><a href='https://www.google.com/maps/search/?api=1&query={map_query}' target='_blank'>View on Google Maps</a>"
                        else:
                            response += "Sorry, I don't have the exact address, but it's in "
                            response += escape(business.city) if business.city else "an unknown location"

                        # Add follow-up question
                        response += "<br><br>Would you like contact information or business hours?"
                        is_html = True
                    else:
                        response = f"I couldn't find information about {escape(business_name)}. Did you mean one of these businesses?"
                        # Try to find similar businesses
                        similar = get_businesses_by_criteria(query=business_name)
                        if similar:
                            response += "<br><br>"
                            for biz in similar[:3]:  # Show max 3 suggestions
                                response += f"- <a href='#' class='suggestion' onclick='sendSuggestion(\"Tell me about {escape(biz.name)}\")'>{escape(biz.name)}</a><br>"
                        is_html = True
                else:
                    response = "Please specify which business you're asking about, for example: 'Where is ABC Hardware located?'"
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

                        # Add follow-up options
                        response += "<br><br>Would you like to know about their products, business hours, or location?"
                        is_html = True
                    else:
                        response = f"Sorry, I couldn't find contact information for {escape(business_name)}"
                        # Try to find similar businesses
                        similar = get_businesses_by_criteria(query=business_name)
                        if similar:
                            response += ". Did you mean one of these?<br><br>"
                            for biz in similar[:3]:
                                response += f"- <a href='#' class='suggestion' onclick='sendSuggestion(\"Contact info for {escape(biz.name)}\")'>{escape(biz.name)}</a><br>"
                        is_html = True
                else:
                    response = "Please specify which business you want contact information for, for example: 'What's the phone number for XYZ Services?'"
                    is_html = False

            elif intent == "categories":
                categories = get_all_categories()
                if categories:
                    response = "<strong>Available business categories:</strong><br>- " + "<br>- ".join(escape(c) for c in categories)
                    response += "<br><br>You can ask about businesses in a specific category, like 'Show me restaurants' or 'List construction companies'."
                    is_html = True
                else:
                    response = "Our category list is currently being updated. You can still search for businesses by name or location."
                    is_html = False

            elif intent == "add_business":
                response = """
                <strong>To add your business to our directory:</strong><br><br>
                1. Visit our business registration page at <a href="/business/register/" target="_blank">/business/register/</a><br>
                2. Fill out the form with your business details<br>
                3. Submit for approval (typically takes 1-2 business days)<br><br>
                <strong>Benefits of registering:</strong>
                <ul>
                    <li>Get discovered by potential customers</li>
                    <li>Showcase your products/services</li>
                    <li>Post updates and special offers</li>
                </ul>
                Would you like me to guide you through the registration process now?
                """
                is_html = True

            elif intent == "product_query":
                if entities.get("business_names") or entities.get("product_names"):
                    business_name = entities["business_names"][0] if entities["business_names"] else None
                    product_query = " ".join(entities["product_names"]) if entities["product_names"] else message

                    # Try to find products
                    product_data = get_business_products(business_name, product_query)

                    if product_data and product_data['products']:
                        business = product_data['business']
                        products = product_data['products']

                        if len(products) == 1:
                            # Single product found
                            product = products[0]
                            response = f"<strong>Here's the product I found at {escape(business.name)}:</strong><br><br>"
                            response += format_product_response(product)

                            # Add follow-up options
                            response += "<br>Would you like to know about other products from this business or their contact information?"
                        else:
                            # Multiple products found
                            response = f"<strong>Here are products I found at {escape(business.name)} matching '{escape(product_query)}':</strong><br><br>"
                            for product in products:
                                response += format_product_response(product) + "<br>"

                            # Add note if results were limited
                            if len(products) == 20:
                                response += "<br><em>Showing first 20 matches. Try a more specific search to narrow results.</em>"

                        # Add link to view all products
                        response += f"<br><a href='/directory/{business.id}/products/' class='business-link'>View all products from {escape(business.name)}</a>"
                        is_html = True
                    else:
                        response = f"I couldn't find any products matching '{escape(product_query)}'"
                        if business_name:
                            response += f" at {escape(business_name)}"

                        # Provide helpful suggestions
                        response += ".<br><br>Try these tips:<br>"
                        response += "- Check your spelling<br>"
                        response += "- Try a broader search term<br>"
                        response += "- Ask about products from a specific business (e.g., 'What products does ABC Store sell?')"
                        is_html = True
                else:
                    response = "Please specify which business's products you're asking about, for example: 'What products does ABC Hardware sell?' or 'Show me laptops at XYZ Electronics'"
                    is_html = False

            elif intent == "business_details":
                if entities["business_names"]:
                    business_name = entities["business_names"][0]
                    details = get_business_full_details(business_name)

                    if details:
                        business = details['business']
                        response = f"<strong>Details about {escape(business.name)}:</strong><br><br>"

                        # Basic info
                        response += f"<div class='business-details'>"
                        if business.category:
                            response += f"<div>🏷️ Category: {escape(business.category.name)}</div>"

                        if business.description:
                            short_desc = business.description[:200] + "..." if len(business.description) > 200 else business.description
                            response += f"<div>📝 Description: {escape(short_desc)}</div>"

                        # Contact info
                        response += "<div class='contact-section'><strong>Contact Information:</strong><br>"
                        if business.phone_number:
                            response += f"📞 <a href='tel:{business.phone_number}'>{escape(business.phone_number)}</a><br>"
                        if business.email:
                            response += f"✉️ <a href='mailto:{business.email}'>{escape(business.email)}</a><br>"
                        if business.website:
                            website_display = escape(business.website.replace('http://', '').replace('https://', ''))
                            response += f"🌐 <a href='{business.website}' target='_blank'>{website_display}</a><br>"
                        if business.address:
                            response += f"📍 {escape(business.address)}"
                            if business.city:
                                response += f", {escape(business.city)}"
                        response += "</div>"

                        # Recent posts
                        if details['recent_posts']:
                            response += "<div class='recent-posts'><strong>Recent Updates:</strong><br>"
                            for post in details['recent_posts']:
                                response += f"<div class='post'>- {escape(post.title)}"
                                if post.post_type:
                                    response += f" ({escape(post.post_type)})"
                                response += "</div>"
                            response += "</div>"

                        response += "</div>"

                        # View more link and follow-up options
                        response += f"<br><a href='/directory/{business.id}/' class='business-link'>View full profile for {escape(business.name)}</a>"
                        response += "<br><br>Would you like to know about their products, business hours, or location?"
                        is_html = True
                    else:
                        response = f"I couldn't find detailed information about {escape(business_name)}. Did you mean one of these businesses?"
                        # Try to find similar businesses
                        similar = get_businesses_by_criteria(query=business_name)
                        if similar:
                            response += "<br><br>"
                            for biz in similar[:3]:  # Show max 3 suggestions
                                response += f"- <a href='#' class='suggestion' onclick='sendSuggestion(\"Tell me about {escape(biz.name)}\")'>{escape(biz.name)}</a><br>"
                        is_html = True
                else:
                    response = "Please specify which business you're asking about, for example: 'Tell me about ABC Hardware' or 'What does XYZ Services offer?'"
                    is_html = False

            else:
                # Fallback for unrecognized queries - try to be helpful
                if len(message.split()) <= 4:
                    # Short query - likely a business name
                    businesses = get_businesses_by_criteria(query=message)
                    if businesses:
                        response = "<strong>Here are some businesses that might match your query:</strong><br><br>"
                        for biz in businesses:
                            response += format_business_result(biz, message)
                        response += "<br>If you were looking for something specific, try being more detailed in your request."
                        is_html = True
                    else:
                        response = f"I'm not sure I understand your request about '{escape(message)}'.<br><br>"
                        response += get_help_response()
                        is_html = True
                else:
                    # Longer query - provide more targeted help
                    response = f"I'm not sure how to help with '{escape(message)}'.<br><br>"

                    if "product" in message.lower():
                        response += "If you're asking about products, try something like:<br>"
                        response += "- 'What products does ABC Store sell?'<br>"
                        response += "- 'Show me laptops at XYZ Electronics'<br>"
                        response += "- 'Is the drill in stock at Hardware Plus?'<br><br>"

                    response += get_help_response()
                    is_html = True

            return JsonResponse({
                'response': response,
                'is_html': is_html
            })

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return JsonResponse({
                'error': "Sorry, I encountered an unexpected error. Please try again or ask your question differently.",
                'is_html': False
            }, status=500)

    return JsonResponse({
        'error': "Invalid request method",
        'is_html': False
    }, status=400)