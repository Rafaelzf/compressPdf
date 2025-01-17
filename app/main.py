# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.routes.pdf import router as pdf_router
import os

# Configurar logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
   handlers=[
       logging.StreamHandler()  
   ]
)

app = FastAPI(
   title="PDF Compressor API",
   description="API para compressão de arquivos PDF",
   version="1.0.0"
)

# Pegar as origins do .env e transformar em lista
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
origins = [origin.strip() for origin in origins]

# Configurar CORS
app.add_middleware(
   CORSMiddleware,
  allow_origins=origins,
   allow_credentials=True,
   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
   allow_methods=["*"],
   allow_headers=["*"],
)

# Incluir as rotas
app.include_router(pdf_router)

@app.get("/")
async def root():
   return {
       "message": "PDF Compression API",
       "docs": "/docs",  # Link para documentação Swagger
       "endpoints": {
           "compress": "/pdf/compress"
       }
   }

if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)