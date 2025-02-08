# Usar imagem Python oficial otimizada
FROM python:3.9-slim

# Configurar variáveis de ambiente essenciais
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV GHOSTSCRIPT_PATH=/usr/bin/gs

# Instalar dependências do sistema incluindo Ghostscript
RUN apt-get update && apt-get install -y \
    ghostscript \
    libgs-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && ghostscript --version

# Configurar diretório de trabalho
WORKDIR /app

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY ./app ./app

# Configurar diretório para uploads temporários
RUN mkdir -p /tmp/pdf_uploads && chmod 777 /tmp/pdf_uploads

# Expor porta da aplicação
EXPOSE 8000

# Configurar verificação de saúde da aplicação
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/ || exit 1

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]