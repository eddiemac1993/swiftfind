# chatbot/apps.py
from django.apps import AppConfig
import spacy

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    nlp = None # Class attribute to hold the loaded model

    def ready(self):
        # This method is called when Django starts
        if not ChatbotConfig.nlp: # Load only once
            try:
                ChatbotConfig.nlp = spacy.load("en_core_web_sm")
                print("spaCy model 'en_core_web_sm' loaded successfully.")
            except OSError:
                print("Could not load spaCy model 'en_core_web_sm'.")
                print("Please ensure it's downloaded: python -m spacy download en_core_web_sm")
                ChatbotConfig.nlp = None # Set to None if loading fails