import random
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Lists of adjectives and nouns to generate random names
ADJECTIVES = [
    'Happy', 'Silly', 'Brave', 'Gentle', 'Clever', 'Witty', 'Fierce', 'Calm', 'Lively', 'Mystic',
    'Swift', 'Bold', 'Shy', 'Wild', 'Quiet', 'Lucky', 'Proud', 'Wise', 'Kind', 'Radiant'
]

NOUNS = [
    'Tiger', 'Eagle', 'Dolphin', 'Phoenix', 'Wolf', 'Lion', 'Bear', 'Fox', 'Owl', 'Dragon',
    'Panther', 'Falcon', 'Shark', 'Griffin', 'Leopard', 'Hawk', 'Orca', 'Raven', 'Cheetah', 'Serpent'
]

def generate_random_name(ip_address):
    """
    Generates a consistent random name based on the user's IP address.

    Args:
        ip_address (str): The user's IP address.

    Returns:
        str: A random name in the format "Adjective Noun".
    """
    cache_key = f'random_name_{ip_address}'
    random_name = cache.get(cache_key)
    if not random_name:
        random.seed(ip_address)
        adjective = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        random_name = f"{adjective} {noun}"
        cache.set(cache_key, random_name, timeout=60 * 60 * 24)  # Cache for 24 hours
        logger.debug(f"Generated random name '{random_name}' for IP '{ip_address}'")
    return random_name

def get_client_ip(request):
    """
    Retrieves the client's IP address from the request.

    Args:
        request (HttpRequest): The Django request object.

    Returns:
        str: The client's IP address.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip