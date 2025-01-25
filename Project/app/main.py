import os
import csv
from datetime import datetime
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from deepface import DeepFace
import base64
import cv2
import numpy as np
import subprocess

# Ejecutar el comando 'pwd' en el sistema
current_directory = subprocess.run(["pwd"], capture_output=True, text=True)
list_directory = subprocess.run(["ls"], capture_output=True, text=True)


# Mostrar el resultado
print(current_directory.stdout.strip())
print(list_directory.stdout.strip())


app = FastAPI()
#Montar la carpeta de archivos esenciales
# CORS y rutas estáticas
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Permitir solicitudes de cualquier origen.
    allow_credentials=True,     # Permitir el uso de cookies y autenticación.
    allow_methods=["*"],        # Permitir cualquier método HTTP (GET, POST, PUT, etc.).
    allow_headers=["*"],        # Permitir cualquier cabecera HTTP personalizada.
)


@app.get("/")
def get_frontend():
    return FileResponse("index.html")

# Crear carpeta para reportes y videos
os.makedirs("Reportes", exist_ok=True)
os.makedirs("Videos", exist_ok=True)


# Variables globales para gestionar el análisis
analyzing = True
emotion_log = [] 
features = []#Cantidad de personas en la imagen
emotion_translation = {
    'angry': 'Enojo',
    'disgust': 'Desagrado',
    'fear': 'Miedo',
    'happy': 'Felicidad',
    'sad': 'Tristeza',
    'surprise': 'Sorpresa',
    'neutral': 'Neutral'
}#Diccionario de emociones

models_FR = [
  "VGG-Face", 
  "Facenet", 
  "Facenet512", 
  "OpenFace", 
  "DeepFace", 
  "DeepID", 
  "ArcFace", 
  "Dlib", 
  "SFace",
  "GhostFaceNet",
]


backends = [
  'opencv', 
  'ssd', 
  'dlib', 
  'mtcnn', 
  'fastmtcnn',
  'retinaface', 
  'mediapipe',
  'yolov8',
  'yunet',
  'centerface',
]

templates = Jinja2Templates(directory="static") 

# Página principal
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
     # Renderiza el archivo index.html desde la carpeta templates
    return templates.TemplateResponse("index.html", {"request": request})

#Modelo entrenado clasificador
haar_cascade = cv2.CascadeClassifier('/app/haar_face.xml')


#Vista del procesamiento
def mostrar_frame(frame,frame2):
    #cv2.imshow("Imagen",frame)
    cv2.imshow('Imagen Recortada',frame2)
    cv2.waitKey(1)


# WebSocket para procesar frames en tiempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global analyzing, emotion_log,start_an
    start_an = datetime.now()
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
            
            #---DETECTORES
            #Extraer la region de interes facial
            try:
                faces_rect = haar_cascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=1)            
                for (x,y,w,h) in faces_rect:
                    faces_roi = frame[y:y+h,x:x+w]#Recortar la imagen
                
                #faces_rect = DeepFace.extract_faces(frame,detector_backend=backends[5], enforce_detection=False) #El B[1-3-5-8(Elimina una parte del ancho y alto es minima)-9(Elimina mas bordes que el primero)]
                #facial_area = faces_rect[0]['facial_area'] 
                #faces_roi = frame[facial_area['y']:facial_area['y'] + facial_area['h'], facial_area['x']:facial_area['x'] + facial_area['w']]
                
                #cv2.rectangle(frame,(x,y),(x+w,y+y),255,thickness=3)
                #mostrar_frame(frame, faces_roi)
                                                                                             
            except Exception as e:
                print(f'Error 1: {e}')
                
                        
            N_personas = str(len(faces_rect)) 

            #await websocket.send_json({"person_detect": value})
            
#Reconocimiento de las emociones
            #Si se desea mas personas unir al bucle anterior
            if analyzing and N_personas == '1':
                try:
                    analysis = DeepFace.analyze(faces_roi, actions=['emotion'])
                    
                    #analysis0 = DeepFace.analyze(frame,actions=['emotion'],detector_backend=backends[0], enforce_detection=False)
                    #analysis2 = DeepFace.analyze(frame,actions=['age','gender',"emotion"])
                    
                    ##print('orden de emm: ', analysis[0]['emotion'])
                    emociones = list((analysis[0]['emotion']).values())
                    emociones = [float(valor) for valor in emociones]
                    #print(f"las emociones son: {emociones}, y su tipo de elemnto es {type(emociones)}" )
                    emotion = analysis[0]["dominant_emotion"]
                    #emotion0 = analysis0[0]["dominant_emotion"]
                    percentage = int(analysis[0]['emotion'][emotion])
                    
                    #Reemplazo de los datos
                    emotion = emotion_translation.get(emotion, emotion)                        

                    if percentage < 10:
                        emotion = 'Desconocida'
                    
                    #data_to_send = {'emotion':emotion,
                    #               'percentage':str(percentage),
                    #               "NumeroPersonas":N_personas,
                    #               'endan':tiempo}   
                    
                    #await websocket.send_json(data_to_send)
                
                except Exception:
                    emotion = "Desconocida"
                    percentage = '0'                
                    
                emotion_log.append({"time": datetime.now().isoformat(), "emotion": emotion})

            else:
                emotion = 'Desconocida'
                percentage = '0'
                emociones = [0,0,0,0,0,0,0]
            try:
                end_an = datetime.now()
                tiempo = str(end_an-start_an)
                data_to_send = {'emotion':emotion,
                               'percentage':percentage,
                               "NumeroPersonas":N_personas,
                               'Tiempo':tiempo,
                               'emociones':emociones}   
                await websocket.send_json(data_to_send)
            except NameError as e:
                return {"message": f"Rostro no encontrado {e}"}
                           
    
        except NameError as e:
            print("Error 2:Conexion Cerrada")
            break
    
    #await websocket.close()


# Ruta para guardar análisis y reporte
@app.post("/save-analysis/")
async def save_analysis(video: UploadFile = File(...)):
    global emotion_log,end_an
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_path = f"Reportes/reporte_{timestamp}.csv"
    video_path = f"Videos/video_{timestamp}.webm"
    
    #video_path = f"Videos/{video.filename}"#captured_video.webm
    
    if not emotion_log:
        return {"message": "No hay datos para guardar"}
    
    
    # Guardar reporte en CSV
    with open(report_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["time", "emotion"])
        writer.writeheader()
        writer.writerows(emotion_log)
    
    #Guardar video en webm
    try:
        file_content = await video.read()
        #print(f"Tipo de contenido: {video.content_type}")
        #print(f"El archivo recibido tiene {len(file_content)} bytes")
        
        if os.path.exists(video_path):
            #print(f'la ruta existente sera: {video_path}')
            with open(video_path, "wb") as f:
                f.write(file_content)
                
            #return {"message": f"Video guardado en {video_path}"}
            emotion_log = []  # Limpiar el log después de guardar
        else:
            with open(video_path, "wb") as f:
                f.write(file_content)
            #print(f'la ruta no existente sera: {video_path}')
                
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
    reports = os.listdir("Reportes/")
    videos = os.listdir("Videos/")
    return {"reports": reports, "videos": videos}
