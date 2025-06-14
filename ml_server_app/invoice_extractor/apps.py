from django.apps import AppConfig

class InvoiceExtractorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoice_extractor'
    
    def ready(self):
        # Import des signaux au démarrage de l'application
        import invoice_extractor.signals