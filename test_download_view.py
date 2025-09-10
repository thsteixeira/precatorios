"""
Test download view for debugging S3 download issues
Add this to urls.py temporarily: path('test-download/<str:precatorio_cnj>/', test_download_view, name='test_download'),
"""
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from precapp.models import Precatorio
import logging

logger = logging.getLogger(__name__)

@login_required  
def test_download_view(request, precatorio_cnj):
    """Ultra-simple test download view"""
    
    # Log the request
    logger.info(f"TEST DOWNLOAD: {precatorio_cnj}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        # Get precatorio
        precatorio = Precatorio.objects.get(cnj=precatorio_cnj)
        
        if not precatorio.integra_precatorio:
            return HttpResponse("No file found", status=404)
        
        file_name = precatorio.integra_precatorio.name
        logger.info(f"File name: {file_name}")
        
        # Try to open file
        file_obj = default_storage.open(file_name, 'rb')
        content = file_obj.read()
        file_obj.close()
        
        logger.info(f"File size read: {len(content)} bytes")
        
        # Create simple response
        response = HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="test_{precatorio_cnj.replace("/", "_")}.pdf"'
        response['Content-Length'] = str(len(content))
        
        logger.info(f"Returning response with {len(content)} bytes")
        return response
        
    except Exception as e:
        logger.error(f"TEST DOWNLOAD ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return HttpResponse(f"Error: {e}", status=500)
