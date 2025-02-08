# app/routes/pdf.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import io
import logging
from app.services.pdf_service import pdf_compressor
from typing import Optional

router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

@router.post("/compress")
async def compress_pdf(
    file: UploadFile = File(...),
    compression_level: Optional[str] = 'screen',
    image_resolution: Optional[int] = 72
):
    """
    Endpoint para compressão de arquivos PDF.
    Recebe um arquivo PDF e retorna sua versão comprimida.
    """
    try:
        # Validar tipo do arquivo
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos PDF são aceitos"
            )
            
        # Comprimir o PDF
        compression_result = await pdf_compressor.compress_pdf_file(
            file=file,
            compression_level=compression_level,
            image_resolution=image_resolution
        )
        
        # Retornar o arquivo comprimido
        return StreamingResponse(
            io.BytesIO(compression_result.compressed_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={compression_result.compressed_name}",
                "X-Original-Size": str(compression_result.original_size),
                "X-Compressed-Size": str(compression_result.compressed_size),
                "X-Compression-Ratio": f"{compression_result.compression_ratio:.2f}%"
            }
        )
        
    except Exception as e:
        logger.error(f"Erro durante a compressão: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro na compressão: {str(e)}"
        )