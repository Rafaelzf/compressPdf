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
    file: UploadFile, 
    compression_level: str = 'screen',
    image_resolution: int = 72
) -> bytes:
   try:
       # Validar o nível de compressão
       valid_levels = ['screen', 'ebook', 'printer', 'prepress', 'default']
       if compression_level not in valid_levels:
           compression_level = 'screen'  # valor padrão se inválido

       # Verificar se o Ghostscript está instalado
       if not os.path.exists(GHOSTSCRIPT_PATH):
           raise ValueError("Ghostscript não encontrado. Por favor, instale-o usando 'brew install ghostscript'")

       with tempfile.TemporaryDirectory() as temp_dir:
           input_path = Path(temp_dir) / "input.pdf"
           output_path = Path(temp_dir) / "output.pdf"
           
           content = await file.read()
           input_size = len(content)
           
           with open(input_path, "wb") as f:
               f.write(content)
           
           logger.info(f"Tamanho original: {input_size / 1024:.2f}KB")
           
           # Configurações avançadas do Ghostscript para melhor compressão
           command = [
            GHOSTSCRIPT_PATH,
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS=/{compression_level}',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-r{image_resolution}',
            # Configurações de compressão de imagem
            '-dColorImageDownsampleType=/Bicubic',
            f'-dColorImageResolution={image_resolution}',
            '-dGrayImageDownsampleType=/Bicubic',
            f'-dGrayImageResolution={image_resolution}',
            '-dMonoImageDownsampleType=/Bicubic',
            f'-dMonoImageResolution={image_resolution}',
            # Compressão JPEG
            '-dAutoFilterColorImages=false',
            '-dColorImageFilter=/DCTEncode',
            '-dAutoFilterGrayImages=false',
            '-dGrayImageFilter=/DCTEncode',
            # Saída
            f'-sOutputFile={output_path}',
            str(input_path)
           ]
           
           try:
               # Log do comando para debug
               logger.info(f"Executando comando: {' '.join(command)}")
               
               process = subprocess.run(
                   command,
                   check=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   text=True
               )
               
               # Log dos outputs
               if process.stdout:
                   logger.info(f"Stdout: {process.stdout}")
               if process.stderr:
                   logger.warning(f"Stderr: {process.stderr}")

           except subprocess.CalledProcessError as e:
               error_msg = (
                   f"Stdout: {e.stdout if e.stdout else 'No stdout'}\n"
                   f"Stderr: {e.stderr if e.stderr else 'No stderr'}\n"
                   f"Return code: {e.returncode}"
               )
               logger.error(f"Erro no Ghostscript: {error_msg}")
               raise ValueError(f"Erro na execução do Ghostscript: {error_msg}")
           
           if not output_path.exists():
               raise ValueError("Falha ao gerar arquivo comprimido")
           
           # Verificar tamanho e validar arquivo comprimido
           with open(output_path, "rb") as f:
               compressed_content = f.read()
           
           output_size = len(compressed_content)
           
           # Verificar se o arquivo está vazio
           if output_size == 0:
               raise ValueError("Arquivo comprimido está vazio")
               
           compression_ratio = (1 - (output_size / input_size)) * 100
           
           logger.info(f"Tamanho final: {output_size / 1024:.2f}KB")
           logger.info(f"Taxa de compressão: {compression_ratio:.2f}%")
           
           # Retornar original se comprimido ficou maior
           if output_size >= input_size:
               logger.warning("Arquivo comprimido ficou maior que o original")
               return content
           
           # Verificar se o PDF é válido
           try:
               with open(output_path, "rb") as f:
                   test_content = f.read(100)
               if not test_content.startswith(b'%PDF'):
                   raise ValueError("Arquivo comprimido não é um PDF válido")
           except Exception as e:
               raise ValueError(f"Arquivo comprimido está corrompido: {str(e)}")
           
           return compressed_content

   except Exception as e:
       logger.error(f"Erro ao processar PDF: {str(e)}")
       raise ValueError(f"Erro ao processar PDF: {str(e)}")