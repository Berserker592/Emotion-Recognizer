from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
import cv2
import numpy as np
import os

app = FastAPI()

# Habilitar CORS para comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta para página estática
app.mount("/static", StaticFiles(directory="/home/paul/Documentos/PROYECTOS/Final_Proyect/static"), name="static")

# Página principal
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>Detección de Emociones</title>
            <link rel="stylesheet" href="styles.css">
        </head>
        <body>
            <h1>Detección de Emociones en Video</h1>
            <form action="/upload-video/" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="video/*">
                <button type="submit">Subir y Analizar</button>
            </form>
        </body>
    </html>
    """

# Ruta para procesar video
@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    # Guardar el archivo temporalmente
    video_path = f"uploaded_{file.filename}"
    with open(video_path, "wb") as f:
        f.write(file.file.read())

    # Procesar el video con DeepFace
    results = process_video(video_path)

    # Eliminar el archivo temporal
    os.remove(video_path)

    return {"results": results}

# Procesa el video usando DeepFace
def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    emotions = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Procesar cada frame con DeepFace
        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotions.append(analysis["dominant_emotion"])
        except Exception as e:
            emotions.append("unknown")

    cap.release()

    # Resumen de emociones detectadas
    emotion_summary = {emotion: emotions.count(emotion) for emotion in set(emotions)}
    return emotion_summary
