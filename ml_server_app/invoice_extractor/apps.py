from django.apps import AppConfig

class InvoiceExtractorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoice_extractor'
    
    def ready(self):
        """
        Initialisation de l'application
        """
        # Import des signaux
        import invoice_extractor.signals