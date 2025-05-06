from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import cv2
from pathlib import Path
import boto3

app = FastAPI()

# Configurar Cloudflare R2 (você preencherá depois)
R2_ACCESS_KEY = "SUA_CHAVE_AQUI"
R2_SECRET_KEY = "SUA_CHAVE_SECRETA_AQUI"
R2_ENDPOINT = "SUA_URL_R2_AQUI"
R2_BUCKET = "framepack-files"

s3 = boto3.client(
    "s3",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    endpoint_url=R2_ENDPOINT
)

# Diretório temporário
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    # Salvar o vídeo temporariamente
    input_path = OUTPUT_DIR / file.filename
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Processar com OpenCV (exemplo simples, substitua pela lógica do FramePack)
    output_path = OUTPUT_DIR / f"processed_{file.filename}"
    cv2_video = cv2.VideoCapture(str(input_path))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, 20.0, (640, 480))
    while cv2_video.isOpened():
        ret, frame = cv2_video.read()
        if not ret:
            break
        out.write(frame)
    cv2_video.release()
    out.release()

    # Fazer upload para R2
    s3.upload_file(str(output_path), R2_BUCKET, f"processed/{file.filename}")

    # Gerar URL do arquivo
    file_url = f"{R2_ENDPOINT}/{R2_BUCKET}/processed/{file.filename}"

    # Limpar arquivos temporários
    os.remove(input_path)
    os.remove(output_path)

    return {"download_url": file_url}

@app.get("/health")
async def health():
    return {"status": "ok"}
