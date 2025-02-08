# scripts/generate_dockerfile.py

class DockerfileBuilder:
    """
    Uma classe personalizada para gerar Dockerfiles de forma programática,
    especialmente adaptada para aplicações Python/FastAPI
    """
    def __init__(self):
        self.instructions = []
    
    def add_instruction(self, instruction, *args):
        """Adiciona uma instrução ao Dockerfile com formatação adequada"""
        if args:
            formatted_args = ' '.join(str(arg) for arg in args)
            self.instructions.append(f"{instruction} {formatted_args}")
        else:
            self.instructions.append(instruction)
    
    def add_comment(self, comment):
        """Adiciona um comentário explicativo ao Dockerfile"""
        self.instructions.append(f"# {comment}")
    
    def generate(self):
        """Gera o conteúdo completo do Dockerfile"""
        return '\n'.join(self.instructions)

def generate_pdf_compressor_dockerfile():
    """
    Gera um Dockerfile otimizado para a aplicação de compressão de PDF
    com todas as configurações e dependências necessárias
    """
    builder = DockerfileBuilder()
    
    # Adicionar instruções com comentários explicativos
    builder.add_comment("Usar imagem Python oficial otimizada")
    builder.add_instruction("FROM python:3.9-slim")
    builder.add_instruction("")
    
    builder.add_comment("Configurar variáveis de ambiente essenciais")
    builder.add_instruction("ENV PYTHONDONTWRITEBYTECODE=1")
    builder.add_instruction("ENV PYTHONUNBUFFERED=1")
    builder.add_instruction("ENV DEBIAN_FRONTEND=noninteractive")
    builder.add_instruction("ENV GHOSTSCRIPT_PATH=/usr/bin/gs")
    builder.add_instruction("")
    
    builder.add_comment("Instalar dependências do sistema incluindo Ghostscript")
    builder.add_instruction("""RUN apt-get update && apt-get install -y \\
    ghostscript \\
    libgs-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/* \\
    && ghostscript --version""")
    builder.add_instruction("")
    
    builder.add_comment("Configurar diretório de trabalho")
    builder.add_instruction("WORKDIR /app")
    builder.add_instruction("")
    
    builder.add_comment("Instalar dependências Python")
    builder.add_instruction("COPY requirements.txt .")
    builder.add_instruction("RUN pip install --no-cache-dir -r requirements.txt")
    builder.add_instruction("")
    
    builder.add_comment("Copiar código da aplicação")
    builder.add_instruction("COPY ./app ./app")
    builder.add_instruction("")
    
    builder.add_comment("Configurar diretório para uploads temporários")
    builder.add_instruction("RUN mkdir -p /tmp/pdf_uploads && chmod 777 /tmp/pdf_uploads")
    builder.add_instruction("")
    
    builder.add_comment("Expor porta da aplicação")
    builder.add_instruction("EXPOSE 8000")
    builder.add_instruction("")
    
    builder.add_comment("Configurar verificação de saúde da aplicação")
    builder.add_instruction('HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/ || exit 1')
    builder.add_instruction("")
    
    builder.add_comment("Comando para iniciar a aplicação")
    builder.add_instruction('CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]')
    
    # Gerar e salvar o Dockerfile
    dockerfile_content = builder.generate()
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    print("Dockerfile gerado com sucesso!")
    print("\nConteúdo do Dockerfile gerado:")
    print(dockerfile_content)

if __name__ == "__main__":
    generate_pdf_compressor_dockerfile()