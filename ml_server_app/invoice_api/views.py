from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from django.conf import settings
from django.http import HttpResponse
import os
import logging
import threading
import json

from .models import Invoice, InvoiceAnnotation, TrainingJob
from .serializers import InvoiceSerializer, InvoiceAnnotationSerializer, TrainingJobSerializer
from .extractors import TextExtractor, TextProcessor

# Importer le nouvel extracteur LayoutLMv3
try:
    from .ml_models import layoutlmv3_extractor
    LAYOUTLMV3_AVAILABLE = True
except ImportError:
    LAYOUTLMV3_AVAILABLE = False
    logging.warning("LayoutLMv3 n'est pas disponible. Certaines fonctionnalités seront limitées.")

logger = logging.getLogger(__name__)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            
            # Extraire le texte de la facture
            file_path = os.path.join(settings.MEDIA_ROOT, invoice.file.name)
            
            # Utiliser LayoutLMv3 si disponible, sinon utiliser l'extracteur classique
            if LAYOUTLMV3_AVAILABLE:
                try:
                    # Extraire d'abord le texte avec l'extracteur classique pour avoir le texte brut
                    extracted_data = TextExtractor.extract_from_file(file_path)
                    
                    # Puis utiliser LayoutLMv3 pour l'extraction structurée
                    layoutlmv3_results = layoutlmv3_extractor.extract_from_image(file_path)
                    
                    # Fusionner les résultats
                    if "error" not in layoutlmv3_results:
                        extracted_data["structured_data"] = layoutlmv3_results
                        extracted_data["extraction_method"] = "layoutlmv3"
                        
                        # Ajouter les scores de confiance s'ils existent
                        if "confidence_scores" in layoutlmv3_results:
                            extracted_data["confidence_scores"] = layoutlmv3_results["confidence_scores"]
                    else:
                        logger.warning(f"Erreur LayoutLMv3: {layoutlmv3_results['error']}. Utilisation de l'extracteur classique.")
                except Exception as e:
                    logger.error(f"Erreur lors de l'utilisation de LayoutLMv3: {str(e)}")
                    extracted_data = TextExtractor.extract_from_file(file_path)
            else:
                extracted_data = TextExtractor.extract_from_file(file_path)
            
            # Enregistrer le texte extrait
            invoice.set_extracted_text(extracted_data)
            
            # Retourner la réponse avec les données extraites
            return Response({
                'status': 'success',
                'message': 'Facture téléchargée et traitée avec succès',
                'invoice': self.get_serializer(invoice).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def extract(self, request, pk=None):
        """
        Endpoint pour extraire à nouveau le texte d'une facture existante
        """
        invoice = self.get_object()
        file_path = os.path.join(settings.MEDIA_ROOT, invoice.file.name)
        
        if not os.path.exists(file_path):
            return Response({
                'status': 'error',
                'message': 'Fichier non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Utiliser LayoutLMv3 si disponible, sinon utiliser l'extracteur classique
        if LAYOUTLMV3_AVAILABLE:
            try:
                # Extraire d'abord le texte avec l'extracteur classique pour avoir le texte brut
                extracted_data = TextExtractor.extract_from_file(file_path)
                
                # Puis utiliser LayoutLMv3 pour l'extraction structurée
                layoutlmv3_results = layoutlmv3_extractor.extract_from_image(file_path)
                
                # Fusionner les résultats
                if "error" not in layoutlmv3_results:
                    extracted_data["structured_data"] = layoutlmv3_results
                    extracted_data["extraction_method"] = "layoutlmv3"
                    
                    # Ajouter les scores de confiance s'ils existent
                    if "confidence_scores" in layoutlmv3_results:
                        extracted_data["confidence_scores"] = layoutlmv3_results["confidence_scores"]
                else:
                    logger.warning(f"Erreur LayoutLMv3: {layoutlmv3_results['error']}. Utilisation de l'extracteur classique.")
            except Exception as e:
                logger.error(f"Erreur lors de l'utilisation de LayoutLMv3: {str(e)}")
                extracted_data = TextExtractor.extract_from_file(file_path)
        else:
            extracted_data = TextExtractor.extract_from_file(file_path)
        
        invoice.set_extracted_text(extracted_data)
        
        return Response({
            'status': 'success',
            'message': 'Texte extrait avec succès',
            'invoice': self.get_serializer(invoice).data
        })
        
    @action(detail=True, methods=['get'])
    def formatted_text(self, request, pk=None):
        """
        Endpoint pour obtenir le texte formaté d'une facture
        """
        from .text_utils import create_invoice_html
        
        invoice = self.get_object()
        extracted_data = invoice.get_extracted_text()
        
        if not extracted_data or "error" in extracted_data:
            return Response({
                'status': 'error',
                'message': 'Aucun texte extrait disponible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Récupérer le texte formaté
        formatted_text = extracted_data.get("formatted_text", "")
        
        # Option pour retourner en HTML
        if request.query_params.get('format') == 'html':
            # Utiliser la fonction utilitaire pour créer le HTML
            html_content = create_invoice_html(extracted_data)
            return HttpResponse(html_content, content_type='text/html')
        
        # Par défaut, retourner en JSON
        return Response({
            'status': 'success',
            'formatted_text': formatted_text,
            'structured_data': extracted_data.get("structured_data", {})
        })
    
    @action(detail=True, methods=['post'])
    def annotate(self, request, pk=None):
        """
        Endpoint pour annoter une facture et entraîner le modèle
        """
        invoice = self.get_object()
        
        # Vérifier que les données nécessaires sont présentes
        if not request.data.get('originalData') or not request.data.get('correctedData'):
            return Response({
                'status': 'error',
                'message': 'Les données originales et corrigées sont requises'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer l'annotation
        try:
            # Créer et sauvegarder l'annotation
            annotation = InvoiceAnnotation(invoice=invoice)
            annotation.original_data = json.dumps(request.data.get('originalData'))
            annotation.corrected_data = json.dumps(request.data.get('correctedData'))
            annotation.save()
            
            # Mettre à jour les données extraites de la facture avec les corrections
            extracted_data = invoice.get_extracted_text()
            if extracted_data:
                extracted_data["structured_data"] = request.data.get('correctedData')
                invoice.set_extracted_text(extracted_data)
            
            # Créer un job d'entraînement si LayoutLMv3 est disponible
            if LAYOUTLMV3_AVAILABLE:
                training_job = TrainingJob.objects.create(
                    status='pending',
                    epochs=3,
                    batch_size=4,
                    learning_rate=5e-5
                )
                training_job.annotations.add(annotation)
                training_job.save()
                
                # Lancer l'entraînement en arrière-plan
                threading.Thread(target=self._train_model, args=(training_job.id,)).start()
                
                return Response({
                    'status': 'success',
                    'message': 'Annotation enregistrée et entraînement lancé',
                    'training_job_id': training_job.id,
                    'annotation_id': annotation.id
                })
            else:
                return Response({
                    'status': 'success',
                    'message': 'Annotation enregistrée avec succès',
                    'annotation_id': annotation.id
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de l'annotation: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'Erreur lors de l\'annotation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response({
            'status': 'success',
            'message': 'Annotation enregistrée avec succès',
            'annotation_id': annotation.id
        })
    
    def _train_model(self, training_job_id):
        """
        Méthode pour entraîner le modèle en arrière-plan
        """
        try:
            training_job = TrainingJob.objects.get(id=training_job_id)
            training_job.status = 'running'
            training_job.save()
            
            # Récupérer les annotations
            annotations = []
            for annotation in training_job.annotations.all():
                # Préparer les données pour l'entraînement
                annotations.append({
                    'image_path': annotation.invoice.file.name,
                    'original_data': annotation.get_original_data(),
                    'corrected_data': annotation.get_corrected_data()
                })
            
            # Entraîner le modèle
            if LAYOUTLMV3_AVAILABLE:
                result = layoutlmv3_extractor.train(
                    annotations,
                    epochs=training_job.epochs,
                    batch_size=training_job.batch_size
                )
                
                # Mettre à jour le job d'entraînement
                if 'error' in result:
                    training_job.status = 'failed'
                    training_job.error_message = result['error']
                else:
                    training_job.status = 'completed'
                    training_job.set_results(result)
                    
                    # Marquer les annotations comme utilisées pour l'entraînement
                    for annotation in training_job.annotations.all():
                        annotation.mark_as_trained()
                
                training_job.save()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement: {str(e)}")
            try:
                training_job = TrainingJob.objects.get(id=training_job_id)
                training_job.status = 'failed'
                training_job.error_message = str(e)
                training_job.save()
            except:
                pass

class InvoiceAnnotationViewSet(viewsets.ModelViewSet):
    queryset = InvoiceAnnotation.objects.all()
    serializer_class = InvoiceAnnotationSerializer
    parser_classes = (JSONParser,)

class TrainingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingJob.objects.all()
    serializer_class = TrainingJobSerializer
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Endpoint pour vérifier le statut d'un job d'entraînement
        """
        training_job = self.get_object()
        
        return Response({
            'status': training_job.status,
            'created_at': training_job.created_at,
            'updated_at': training_job.updated_at,
            'annotations_count': training_job.annotations.count(),
            'results': training_job.get_results(),
            'error_message': training_job.error_message
        })

# La classe MLViewSet a été déplacée vers ml_views.py