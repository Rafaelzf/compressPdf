# app/services/pdf_service.py
import subprocess
import tempfile
import os
from fastapi import UploadFile
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class CompressionResult:
    """Classe para armazenar os resultados da compressão"""
    compressed_content: bytes
    original_size: int
    compressed_size: int
    compression_ratio: float
    original_name: str
    compressed_name: str

class PDFCompressor:
    """Classe para gerenciar a compressão de PDFs usando Ghostscript"""
    
    def __init__(self):
        # Definir caminho do Ghostscript baseado no ambiente
        self.ghostscript_path = self._find_ghostscript()
        
    def _find_ghostscript(self) -> str:
        """Localiza o executável do Ghostscript no sistema"""
        default_path = '/usr/local/bin/gs'
        if os.path.exists(default_path):
            return default_path
            
        alternative_paths = [
            '/opt/homebrew/bin/gs',
            '/usr/bin/gs',
            '/usr/local/Cellar/ghostscript/*/bin/gs'
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                return path
                
        raise RuntimeError("Ghostscript não encontrado no sistema")

    def _get_ghostscript_command(self, input_path: str, output_path: str, 
                               compression_level: str = 'screen',
                               image_resolution: int = 72) -> list:
        """Gera o comando do Ghostscript com os parâmetros de compressão"""
        return [
            self.ghostscript_path,
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
            str(input_path)
        ]

    async def compress_pdf_file(self, file: UploadFile,
                              compression_level: str = 'screen',
                              image_resolution: int = 72) -> CompressionResult:
        """
        Comprime um arquivo PDF recebido via upload
        Retorna um objeto CompressionResult com os dados da compressão
        """
        try:
            # Criar diretório temporário para processar o arquivo
            with tempfile.TemporaryDirectory() as temp_dir:
                # Preparar caminhos dos arquivos
                temp_dir_path = Path(temp_dir)
                input_path = temp_dir_path / file.filename
                output_path = temp_dir_path / f"compressed_{file.filename}"
                
                # Salvar arquivo original
                content = await file.read()
                input_path.write_bytes(content)
                original_size = len(content)
                
                logger.info(f"Arquivo recebido: {file.filename}")
                logger.info(f"Tamanho original: {original_size / 1024:.2f}KB")
                
                # Executar compressão
                command = self._get_ghostscript_command(
                    str(input_path), 
                    str(output_path),
                    compression_level,
                    image_resolution
                )
                
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
                
                # Ler arquivo comprimido
                if not output_path.exists():
                    raise ValueError("Falha ao gerar arquivo comprimido")
                    
                compressed_content = output_path.read_bytes()
                compressed_size = len(compressed_content)
                
                # Calcular taxa de compressão
                compression_ratio = (1 - (compressed_size / original_size)) * 100
                
                logger.info(f"Compressão concluída:")
                logger.info(f"Arquivo original: {file.filename}")
                logger.info(f"Tamanho original: {original_size / 1024:.2f}KB")
                logger.info(f"Tamanho final: {compressed_size / 1024:.2f}KB")
                logger.info(f"Taxa de compressão: {compression_ratio:.2f}%")
                
                # Se o arquivo comprimido for maior, usar o original
                if compressed_size >= original_size:
                    logger.warning("Arquivo comprimido maior que original, retornando original")
                    return CompressionResult(
                        compressed_content=content,
                        original_size=original_size,
                        compressed_size=original_size,
                        compression_ratio=0,
                        original_name=file.filename,
                        compressed_name=file.filename
                    )
                
                return CompressionResult(
                    compressed_content=compressed_content,
                    original_size=original_size,
                    compressed_size=compressed_size,
                    compression_ratio=compression_ratio,
                    original_name=file.filename,
                    compressed_name=f"compressed_{file.filename}"
                )
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no Ghostscript: {e.stderr}")
            raise ValueError(f"Erro na compressão: {e.stderr}")
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            raise ValueError(f"Erro ao processar PDF: {str(e)}")

# Criar uma instância global do compressor
pdf_compressor = PDFCompressor()