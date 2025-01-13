# app/routes/pdf.py
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
import io
import logging
from app.services.pdf_service import compress_pdf
from pathlib import Path
from pathlib import Path
import tempfile

UPLOAD_DIR = Path(tempfile.gettempdir()) / "pdf_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Configurar o router
router = APIRouter(
   prefix="/pdf",
   tags=["PDF"],
   responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.post("/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    fileName: str = Form(...)
):
    logger = logging.getLogger(__name__)
    try:
        logger.info("Recebendo requisição de chunk")
        logger.info(f"Headers recebidos: {chunk.headers}")
        logger.info(f"Parâmetros: chunkIndex={chunkIndex}, totalChunks={totalChunks}, fileName={fileName}")
        logger.info(f"Iniciando upload do chunk {chunkIndex + 1}/{totalChunks} para arquivo {fileName}")
        logger.info(f"Tamanho do chunk: {len(await chunk.read()) / 1024:.2f}KB")
        await chunk.seek(0)  # Reset the file pointer after reading

        if not chunk:
            logger.error("Nenhum chunk recebido")
            raise HTTPException(status_code=400, detail="Nenhum arquivo recebido")



        # Criar diretório para os chunks deste arquivo
        file_dir = UPLOAD_DIR / fileName
        logger.info(f"Criando diretório para chunks: {file_dir}")
        file_dir.mkdir(exist_ok=True)

        # Salvar chunk
        chunk_path = file_dir / f"chunk_{chunkIndex}"
        logger.info(f"Salvando chunk em: {chunk_path}")
        content = await chunk.read()
        chunk_path.write_bytes(content)

        # Verificar se todos os chunks foram recebidos
        existing_chunks = len(list(file_dir.glob("chunk_*")))
        logger.info(f"Chunks recebidos até agora: {existing_chunks}/{totalChunks}")

        # Calcular progresso
        progress = (existing_chunks / totalChunks) * 100
        logger.info(f"Progresso do upload: {progress:.1f}%")

        # Verificar integridade
        if chunk_path.exists():
           chunk_size = chunk_path.stat().st_size
           logger.info(f"Chunk salvo com sucesso. Tamanho no disco: {chunk_size / 1024:.2f}KB")
        else:
           logger.error(f"Falha ao salvar chunk: arquivo não encontrado em {chunk_path}")
           raise ValueError("Falha ao salvar chunk")
        
        response = {
           "success": True,
           "chunksReceived": existing_chunks,
           "totalChunks": totalChunks,
           "progress": f"{progress:.1f}%",
           "chunkSize": f"{chunk_size / 1024:.2f}KB"
       }
        
        logger.info(f"Upload do chunk concluído: {response}")
        return response

    except Exception as e:
       logger.error(f"Erro no upload do chunk: {str(e)}", exc_info=True)
       logger.error(f"Detalhes do erro - Chunk: {chunkIndex}, fileName: {fileName}")
       raise HTTPException(
           status_code=500, 
           detail=f"Erro no upload do chunk {chunkIndex}: {str(e)}"
       )
    finally:
       logger.info(f"Finalizando processamento do chunk {chunkIndex}/{totalChunks}")

@router.post("/compress/{fileName}")
async def compress_complete_file(fileName: str):
   logger = logging.getLogger(__name__)
   logger.info(f"Iniciando compressão do arquivo {fileName}")

   try:
       file_dir = UPLOAD_DIR / fileName
       output_path = file_dir / "complete.pdf"

       logger.info(f"Diretório dos chunks: {file_dir}")
       logger.info(f"Caminho do arquivo final: {output_path}")

       # Juntar todos os chunks
       logger.info("Iniciando junção dos chunks...")
       with open(output_path, 'wb') as output_file:
           chunks = sorted(file_dir.glob("chunk_*"), 
                         key=lambda x: int(x.name.split('_')[1]))
           
           total_chunks = len(chunks)
           logger.info(f"Total de chunks encontrados: {total_chunks}")

           total_size = 0
           for i, chunk_path in enumerate(chunks, 1):
               chunk_size = chunk_path.stat().st_size
               total_size += chunk_size
               chunk_content = chunk_path.read_bytes()
               output_file.write(chunk_content)
               logger.info(f"Chunk {i}/{total_chunks} processado - Tamanho: {chunk_size/1024:.2f}KB")

       logger.info(f"Arquivo completo montado. Tamanho total: {total_size/1024:.2f}KB")

       # Comprimir o arquivo completo
       logger.info("Iniciando compressão do arquivo...")

       compressed_buffer = await compress_pdf(
           output_path,
           compression_level='screen',
           image_resolution=72
       )
       compressed_size = len(compressed_buffer)
       compression_ratio = ((total_size - compressed_size) / total_size) * 100
       logger.info(f"Compressão concluída. Novo tamanho: {compressed_size/1024:.2f}KB")
       logger.info(f"Taxa de compressão: {compression_ratio:.2f}%")

       # Limpar arquivos temporários
       logger.info("Iniciando limpeza dos arquivos temporários...")
       chunks_removed = 0
       for chunk in file_dir.glob("chunk_*"):
           chunk.unlink()
           chunks_removed += 1
       logger.info(f"Chunks removidos: {chunks_removed}")
       
       output_path.unlink()
       file_dir.rmdir()
       logger.info("Limpeza concluída")

       logger.info("Preparando resposta para download...")
       return StreamingResponse(
           io.BytesIO(compressed_buffer),
           media_type="application/pdf",
           headers={
               "Content-Disposition": f"attachment; filename=compressed_{fileName}"
           }
       )

   except Exception as e:
       logger.error(f"Erro durante a compressão: {str(e)}", exc_info=True)
       
       # Limpar arquivos em caso de erro
       try:
           if file_dir.exists():
               logger.info("Limpando arquivos temporários após erro...")
               files_removed = 0
               for file in file_dir.glob("*"):
                   file.unlink()
                   files_removed += 1
               file_dir.rmdir()
               logger.info(f"Arquivos temporários removidos: {files_removed}")
       except Exception as cleanup_error:
           logger.error(f"Erro durante limpeza: {str(cleanup_error)}")
           
       raise HTTPException(
           status_code=500, 
           detail=f"Erro na compressão: {str(e)}"
       )