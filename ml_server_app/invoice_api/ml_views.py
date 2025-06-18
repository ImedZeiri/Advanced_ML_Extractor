from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
import os
import logging

from .models import InvoiceAnnotation, TrainingJob

# Vérifier si LayoutLMv3 est disponible
try:
    from .ml_models import layoutlmv3_extractor
    LAYOUTLMV3_AVAILABLE = True
except ImportError:
    LAYOUTLMV3_AVAILABLE = False
    logging.warning("LayoutLMv3 n'est pas disponible. Certaines fonctionnalités seront limitées.")

@api_view(['GET'])
def model_info(request):
    """
    Endpoint pour obtenir des informations sur le modèle
    """
    # Récupérer des informations sur le modèle
    model_path = os.path.join(settings.BASE_DIR, 'invoice_api', 'models', 'layoutlmv3')
    model_exists = os.path.exists(model_path)
    
    # Compter les annotations
    total_annotations = InvoiceAnnotation.objects.count()
    trained_annotations = InvoiceAnnotation.objects.filter(used_for_training=True).count()
    
    # Compter les jobs d'entraînement
    total_jobs = TrainingJob.objects.count()
    completed_jobs = TrainingJob.objects.filter(status='completed').count()
    failed_jobs = TrainingJob.objects.filter(status='failed').count()
    
    return Response({
        'status': 'success',
        'model_available': LAYOUTLMV3_AVAILABLE,
        'model_exists': model_exists,
        'annotations': {
            'total': total_annotations,
            'trained': trained_annotations,
            'untrained': total_annotations - trained_annotations
        },
        'training_jobs': {
            'total': total_jobs,
            'completed': completed_jobs,
            'failed': failed_jobs,
            'pending_or_running': total_jobs - completed_jobs - failed_jobs
        }
    })

@api_view(['POST'])
def reset_model(request):
    """
    Endpoint pour réinitialiser le modèle LayoutLMv3
    """
    try:
        # Importer le singleton
        from .ml_models import layoutlmv3_extractor
        
        # Réinitialiser le processeur et le modèle
        layoutlmv3_extractor.processor = None
        layoutlmv3_extractor.model = None
        
        # Recharger le modèle avec les bons paramètres
        layoutlmv3_extractor.load_model()
        
        return Response({
            'status': 'success',
            'message': 'Modèle réinitialisé avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du modèle: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Erreur lors de la réinitialisation du modèle: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def export_annotations(request):
    """
    Endpoint pour exporter toutes les annotations au format JSON
    """
    annotations = []
    
    for annotation in InvoiceAnnotation.objects.all():
        annotations.append({
            'id': annotation.id,
            'invoice_id': annotation.invoice.id,
            'invoice_file': annotation.invoice.file.name,
            'created_at': annotation.created_at.isoformat(),
            'original_data': annotation.get_original_data(),
            'corrected_data': annotation.get_corrected_data(),
            'used_for_training': annotation.used_for_training,
            'training_date': annotation.training_date.isoformat() if annotation.training_date else None
        })
    
    return Response({
        'status': 'success',
        'count': len(annotations),
        'annotations': annotations
    })

@api_view(['GET'])
def training_status(request, job_id):
    """
    Endpoint pour vérifier le statut d'un job d'entraînement
    """
    try:
        training_job = TrainingJob.objects.get(id=job_id)
        
        return Response({
            'status': 'success',
            'job_status': training_job.status,
            'created_at': training_job.created_at,
            'updated_at': training_job.updated_at,
            'annotations_count': training_job.annotations.count(),
            'results': training_job.get_results(),
            'error_message': training_job.error_message
        })
    except TrainingJob.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'Job d\'entraînement {job_id} non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut du job d'entraînement: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Erreur lors de la récupération du statut du job d\'entraînement: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)