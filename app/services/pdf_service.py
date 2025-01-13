# app/services/pdf_service.py
import subprocess
import tempfile
import os
from fastapi import UploadFile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Caminho do Ghostscript no Mac (instalado via Homebrew)
GHOSTSCRIPT_PATH = '/usr/local/bin/gs'  # caminho padrão
if not os.path.exists(GHOSTSCRIPT_PATH):
   # Tenta encontrar em outros locais comuns
   alternative_paths = [
       '/opt/homebrew/bin/gs',
       '/usr/bin/gs',
       '/usr/local/Cellar/ghostscript/*/bin/gs'
   ]
   for path in alternative_paths:
       if os.path.exists(path):
           GHOSTSCRIPT_PATH = path
           break

async def compress_pdf(
    file_path: Path,
    compression_level: str = 'screen',
    image_resolution: int = 72
) -> bytes:
  try:
        # Verificar se o arquivo existe
        if not file_path.exists():
            raise ValueError(f"Arquivo não encontrado: {file_path}")

        # Ler arquivo original
        with open(file_path, 'rb') as f:
            input_buffer = f.read()
            
        logger.info(f"Tamanho original: {len(input_buffer) / 1024:.2f}KB")

        # Criar diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.pdf"
            
            # Configurar comando Ghostscript
            command = [
                GHOSTSCRIPT_PATH,
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS=/{compression_level}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-r{image_resolution}',
                '-dColorImageDownsampleType=/Bicubic',
                f'-dColorImageResolution={image_resolution}',
                '-dGrayImageDownsampleType=/Bicubic',
                f'-dGrayImageResolution={image_resolution}',
                '-dMonoImageDownsampleType=/Bicubic',
                f'-dMonoImageResolution={image_resolution}',
                '-dAutoFilterColorImages=false',
                '-dColorImageFilter=/DCTEncode',
                '-dAutoFilterGrayImages=false',
                '-dGrayImageFilter=/DCTEncode',
                f'-sOutputFile={output_path}',
                str(file_path)
            ]
            
            # Executar compressão
            logger.info("Iniciando compressão...")
            process = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.stderr:
                logger.warning(f"Avisos do Ghostscript: {process.stderr}")

            # Verificar e ler arquivo comprimido
            if not output_path.exists():
                raise ValueError("Falha ao gerar arquivo comprimido")

            with open(output_path, "rb") as f:
                compressed_content = f.read()
            
            # Calcular taxa de compressão
            output_size = len(compressed_content)
            compression_ratio = (1 - (output_size / len(input_buffer))) * 100
            
            logger.info(f"Tamanho final: {output_size / 1024:.2f}KB")
            logger.info(f"Taxa de compressão: {compression_ratio:.2f}%")
            
            # Retornar original se não houver compressão efetiva
            if output_size >= len(input_buffer):
                logger.warning("Arquivo comprimido maior que original, retornando original")
                return input_buffer
            
            return compressed_content

  except subprocess.CalledProcessError as e:
        logger.error(f"Erro no Ghostscript: {e.stderr}")
        raise ValueError(f"Erro na compressão: {e.stderr}")
  except Exception as e:
        logger.error(f"Erro ao processar PDF: {str(e)}")
        raise ValueError(f"Erro ao processar PDF: {str(e)}")