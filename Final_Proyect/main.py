import os
import csv
from datetime import datetime
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from deepface import DeepFace
import base64
import cv2
import numpy as np


app = FastAPI()

#Montar la carpeta de archivos esenciales
app.mount("/static", StaticFiles(directory="/home/paul/Documentos/PROYECTOS/Final_Proyect/static"), name="static")


# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Permitir solicitudes de cualquier origen.
    allow_credentials=True,     # Permitir el uso de cookies y autenticación.
    allow_methods=["*"],        # Permitir cualquier método HTTP (GET, POST, PUT, etc.).
    allow_headers=["*"],        # Permitir cualquier cabecera HTTP personalizada.
)


# Crear carpeta para reportes y videos
os.makedirs("reports", exist_ok=True)
os.makedirs("videos", exist_ok=True)


# Variables globales para gestionar el análisis
analyzing = True
emotion_log = [] 
features = []#Cantidad de personas en la imagen
emotion_translation = {
    'fear': 'Miedo',
    'happy': 'Felicidad',
    'sad': 'Tristeza',
    'angry': 'Enojo',
    'surprise': 'Sorpresa',
    'disgust': 'Desagrado',
    'neutral': 'Neutral'
}#Diccionario de emociones


# Página principal
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>Detección de Emociones en Tiempo Real</title>

        </head>
        <body>
            
            <h1>Detección de Emociones en Tiempo Real</h1>
            <button onclick="startStream()">Iniciar Análisis</button>
            <button id="saveButton" onclick="stopRecording() disabled">Guardar</button>
            <button id="toggle-btn" onclick="toggleAnalysis()">Pausar</button>
            <button onclick="fetchReports()">Ver Reportes</button>
            
            <video id="video" autoplay></video>
            <p id="person_detect">Persona detectada: Ninguna</p>
            <p id="emotion">Emoción detectada: Ninguna</p>
            <ul id="report-list"></ul>

            <script src="static/script.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>

            <canvas id="emotionChart" width="400" height="200"></canvas>

            
        </body>
    </html>
    """

#Modelo entrenado clasificador
haar_cascade = cv2.CascadeClassifier('/home/paul/Documentos/PROYECTOS/haar_face.xml')


#Vista del procesamiento
def mostrar_frame(frame,frame2):
    cv2.imshow("Imagen",frame)
    cv2.imshow('Imagen Recortada',frame2)
    cv2.waitKey(1)


# WebSocket para procesar frames en tiempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global analyzing, emotion_log
    await websocket.accept()
    
    while True:
        try:
            # Recibir frame en base64
            frame_data = await websocket.receive_text()
            frame_data = frame_data.split(",")[1]  # Eliminar encabezado del base64
            frame_bytes = base64.b64decode(frame_data)

            # Convertir el frame a imagen
            np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            
            # Detectar un rostro
            img_gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces_rect = haar_cascade.detectMultiScale(img_gray, scaleFactor=1.1, minNeighbors=2)            
            for (x,y,w,h) in faces_rect:
                faces_roi = frame[y:y+h,x:x+w]#Recortar la imagen
                
                #cv2.rectangle(frame,(x,y),(x+w,y+y),255,thickness=3)
                #mostrar_frame(frame,faces_roi)
                        
            #print(f'Numero de rostro encontrados {len(faces_rect)}')
            #print(faces_rect)
            
            #    if len(faces_rect) ==1:
            #        value = 'Si'                
            #    else:
            #        value = 'No'
            #await websocket.send_json({"person_detect": value})
            
            #Face_detect = DeepFace.extract_faces(frame,detector_backend='opencv')
            #print('Se detecto un rostro, : ',Face_detect)
        

#Reconocimiento de las emociones
            if analyzing:
                try:
                    analysis = DeepFace.analyze(faces_roi, actions=['emotion'], enforce_detection=False)
                    emotion = analysis[0]["dominant_emotion"]
                    percentage = analysis[0]['emotion'][emotion]
                    emotion = emotion_translation.get(emotion, emotion)                        
                        
                    #emotion = f'{emotion} : {str(percentage)}'                
                except Exception:
                    emotion = "Desconocida"

                emotion_log.append({"time": datetime.now().isoformat(), "emotion": emotion})
                await websocket.send_json({"emotion": emotion})

        except Exception as e:
            print("Error:", e)
            break
    #await websocket.close()


# Ruta para guardar análisis y reporte
@app.post("/save-analysis/")
async def save_analysis(video: UploadFile = File(...)):
    global emotion_log
    
    video_path = f"videos/{video.filename}"#captured_video.webm
    if not emotion_log:
        return {"message": "No hay datos para guardar"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_day = datetime.now().strftime("%Y%m%d")

    report_path = f"reports/report_{timestamp}.csv"
    video_name = f"captured_video_{timestamp}.webm"
    video_path = f"videos/{video_name}"
    
    video_route = f"videos/captured_video_{timestamp_day}"

    # Guardar reporte en CSV
    with open(report_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["time", "emotion"])
        writer.writeheader()
        writer.writerows(emotion_log)
    
    try:
        #print(f"Tipo de contenido: {video.content_type}")
        file_content = await video.read()
        #print(f"El archivo recibido tiene {len(file_content)} bytes")
        
        if os.path.exists(video_route):
            print(f'la ruta existente sera: {video_route}')
            with open(video_path, "ab") as f:
                f.write(file_content)
                
            #return {"message": f"Video guardado en {video_path}"}
            emotion_log = []  # Limpiar el log después de guardar
        else:
            print(f'la ruta no existente sera: {video_route}')
            with open(video_route, "wb") as f:
                f.write(file_content)
                
            #return {"message": f"Video guardado en {video_path}"}
            emotion_log = []  # Limpiar el log después de guardar
                 
        return {"message": f"Reporte guardado en {report_path}, Video guardado en {video_path}"}
        
    except Exception as e:
        return {"message": f"Error al guardar el video: {str(e)}"}   

#    emotion_log = []  # Limpiar el log después de guardar
#    return {"message": f"Reporte guardado en {report_path}, Video guardado en {video_path}"}



#@app.post("/upload-video/")
#async def upload_video(video: UploadFile = File(...)):
#    video_path = f"videos/{video.filename}"
#    try:
#        with open(video_path, "wb") as f:
#            f.write(await video.read())
#        return {"message": f"Video guardado en {video_path}"}
#    except Exception as e:
#        return {"message": f"Error al guardar el video: {str(e)}"}


@app.get("/list-reports/")
async def list_reports():
    reports = os.listdir("reports/")
    videos = os.listdir("videos/")
    return {"reports": reports, "videos": videos}
