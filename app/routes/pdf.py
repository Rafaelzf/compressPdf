# app/routes/pdf.py
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
import io
import logging
from app.services.pdf_service import compress_pdf

# Configurar o router
router = APIRouter(
   prefix="/pdf",
   tags=["PDF"],
   responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.post("/compress", 
   summary="Comprimir PDF",
   description="""
   Comprime um arquivo PDF.
   
   - compression_level: Nível de compressão (screen, ebook, printer, prepress)
   - image_resolution: Resolução das imagens (72-300 dpi)
   """
)
async def compress_pdf_route(
   file: UploadFile = File(..., description="Arquivo PDF para comprimir"),
   compression_level: str = Query(
       'screen',
       enum=['screen', 'ebook', 'printer', 'prepress', 'default'],
       description="Nível de compressão do PDF"
   ),
   image_resolution: int = Query(
       72, 
       ge=72, 
       le=300,
       description="Resolução das imagens em DPI"
   )
):
   try:
       # Validar extensão do arquivo
       if not file.filename.endswith('.pdf'):
           raise HTTPException(
               status_code=400,
               detail="O arquivo deve ser um PDF"
           )

       # Comprimir o PDF
       compressed_buffer = await compress_pdf(
           file, 
           compression_level=compression_level,
           image_resolution=image_resolution
       )
       
       # Retornar o arquivo comprimido
       return StreamingResponse(
           io.BytesIO(compressed_buffer),
           media_type="application/pdf",
           headers={
               "Content-Disposition": f"attachment; filename=compressed_{file.filename}"
           }
       )

   except ValueError as e:
       logger.error(f"Erro de validação: {str(e)}")
       raise HTTPException(status_code=400, detail=str(e))
   except Exception as e:
       logger.error(f"Erro não tratado: {str(e)}")
       raise HTTPException(
           status_code=500,
           detail=f"Erro interno ao processar o PDF: {str(e)}"
       )