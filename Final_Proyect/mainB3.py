import os
import csv
from datetime import datetime
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
import base64
import cv2
import numpy as np


app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear carpeta para reportes y videos
os.makedirs("reports", exist_ok=True)
os.makedirs("videos", exist_ok=True)


# Variables globales para gestionar el análisis
analyzing = True
emotion_log = [] 

# Página principal
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>Detección de Emociones en Tiempo Real</title>
            <script>
                let ws;
                let isAnalyzing = true;
                let mediaRecorder;
                let recordedChunks = [];
                let isRecording = false; // Nuevo estado para controlar la grabación

                
                function startStream() {
                    ws = new WebSocket("ws://127.0.0.1:8000/ws");
                    const video = document.querySelector("#video");
                    const canvas = document.createElement("canvas");
                    const context = canvas.getContext("2d");

                    navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(stream => {
                        video.srcObject = stream;
                        video.play();
                        
                        // Configuración para grabar el video
                        mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });
                        mediaRecorder.ondataavailable = event => {
                            if (event.data.size > 0) {
                                recordedChunks.push(event.data);
                            }
                        };
                        
                        //Iniciar grabacion
                        mediaRecorder.start();
                        isRecording = true; // Cambiar estado de grabación a "en grabación"
                        console.log("Grabación iniciada");
                        
                        setInterval(() => {
                            if (isAnalyzing) {
                                canvas.width = video.videoWidth;
                                canvas.height = video.videoHeight;
                                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                                const frame = canvas.toDataURL("image/jpeg");
                                ws.send(frame);
                            }
                        }, 200);// Envía frames cada 200ms
                    });

                    ws.onmessage = event => {
                        const data = JSON.parse(event.data);
                        document.querySelector("#emotion").innerText = "Emoción detectada: " + data.emotion;
                    };
                }


                function toggleAnalysis() {
                    isAnalyzing = !isAnalyzing;
                    document.querySelector("#toggle-btn").innerText = isAnalyzing ? "Pausar" : "Reanudar";

                    if (isAnalyzing && !isRecording) {
                        // Si el análisis se reanuda, reanudar la grabación si estaba detenida
                        mediaRecorder.start();
                        isRecording = true;
                        console.log("Grabación reanudada");
                    } else if (!isAnalyzing && isRecording) {
                        // Si el análisis se pausa, detener la grabación
                        mediaRecorder.stop();
                        isRecording = false;
                        console.log("Grabación pausada");
                    }   
                }
                
                function stopRecording() {
                    if (mediaRecorder.state === "recording") {
                        mediaRecorder.stop();
                    }
                    const videoBlob = new Blob(recordedChunks, { type: "video/webm" });
                    const formData = new FormData();
                    formData.append("video", videoBlob, "captured_video.webm");
            
                    fetch("http://127.0.0.1:8000/save-analysis/", {
                        method: "POST",
                        body: formData,
                    })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message);
                        });
                }
                
                function fetchReports() {
                    fetch("http://127.0.0.1:8000/list-reports/")
                        .then(response => response.json())
                        .then(data => {
                            const reportList = document.querySelector("#report-list");
                            reportList.innerHTML = "";
            
                            data.reports.forEach(report => {
                                const li = document.createElement("li");
                                li.innerHTML = `<a href="http://127.0.0.1:8000/reports/${report}" target="_blank">${report}</a>`;
                                reportList.appendChild(li);
                            });
            
                            data.videos.forEach(video => {
                                const li = document.createElement("li");
                                li.innerHTML = `<a href="http://127.0.0.1:8000/videos/${video}" target="_blank">${video}</a>`;
                                reportList.appendChild(li);
                            });
                        });
                }
                          
            </script>
        </head>
        <body>
            <h1>Detección de Emociones en Tiempo Real</h1>
            <button onclick="startStream()">Iniciar Análisis</button>
            <button onclick="stopRecording()">Guardar</button>
            <button onclick="fetchReports()">Ver Reportes</button>
            
            <button id="toggle-btn" onclick="toggleAnalysis()">Pausar</button>
            <video id="video" autoplay></video>
            <p id="emotion">Emoción detectada: Ninguna</p>
            <ul id="report-list"></ul>

        </body>
    </html>
    """

# WebSocket para procesar frames en tiempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global analyzing, emotion_log
    await websocket.accept()
    
    while True:
        #print('Imagen Recibida',i++1)
        try:
            # Recibir frame en base64
            frame_data = await websocket.receive_text()
            frame_data = frame_data.split(",")[1]  # Eliminar encabezado del base64
            frame_bytes = base64.b64decode(frame_data)

            # Convertir el frame a imagen
            np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

#---OPCION2
            if analyzing:
                try:
                    analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emotion = analysis[0]["dominant_emotion"]
                except Exception:
                    emotion = "Desconocida"

                emotion_log.append({"time": datetime.now().isoformat(), "emotion": emotion})
                await websocket.send_json({"emotion": emotion})

#---OPCION1
#            # Procesar frame con DeepFace
#            try:
#                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
#                emotion = analysis[0]['dominant_emotion']
#                print('La emocion detectada fue',emotion)
#                
#                               
#                Plane = DeepFace.extract_faces(frame,detector_backend='opencv')
#                x=list(Plane[0]['facial_area'].values())[0]
#                y=list(Plane[0]['facial_area'].values())[1]
#                w=list(Plane[0]['facial_area'].values())[2]
#                h=list(Plane[0]['facial_area'].values())[3]
#                #frame = cv2.rectangle(frame,(x,y),(x+w,h+y),(255,255,255),thickness=3)
#                                                   
#            except Exception:
#                emotion = "Desconocida"
#
#            # Enviar emoción detectada al cliente
#            await websocket.send_json({"emotion": emotion})

        except Exception as e:
            print("Error:", e)
            break
    #await websocket.close()

# Ruta para guardar análisis y reporte
@app.post("/save-analysis/")
async def save_analysis(video: UploadFile = File(...)):
    video_path = f"videos/{video.filename}"#captured_video.webm
    
   #print(f'la primera ruta del video es: {video_path}')
    global emotion_log

    if not emotion_log:
        return {"message": "No hay datos para guardar"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/report_{timestamp}.csv"
    video_name = f"captured_video_{timestamp}.webm"
    video_path = f"videos/{video_name}"

    # Guardar reporte en CSV
    with open(report_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["time", "emotion"])
        writer.writeheader()
        writer.writerows(emotion_log)

    # Guardar video asociado
    i=0
    #if os.path.exists(f"videos/captured_video.webm"):
    #    #while os.path.exists(f"videos/captured_video_{i}.webm"):
    #    i=+1
    #    #video_path = f'videos/captured_video_{i}.webm'
    #    #print(f'el nombre del archivo cambio por: {video_path}')
    #    os.rename("videos/captured_video.webm", video_path)
    #            
    #    print(f'la ruta seleccionado sera: {video_path}')     
    #else:
    #    return {"message": "No se encontró el archivo de video para guardar."}
    
    try:
        #print(f"Tipo de contenido: {video.content_type}")
        file_content = await video.read()
        #print(f"El archivo recibido tiene {len(file_content)} bytes")
        
        with open(video_path, "wb") as f:
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
