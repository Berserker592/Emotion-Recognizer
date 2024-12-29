import cv2
from deepface import DeepFace
import pandas as pd
from collections import Counter

def analyze_video(video_source=0, output_csv="/home/paul/Documentos/PROYECTOS/Final_Proyect/emotion_report.csv"):
    # Inicializa la captura de video
    cap = cv2.VideoCapture(video_source)
    emotion_data = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Procesa el frame con DeepFace
            try:
                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
                #print('la emocion detectada fue :',analysis)
                # Acceder a las emociones:
                #dominant_emotion = emotion_data['dominant_emotion']
                #sadness_level = emotion_data['emotion']['sad']
                #fear_level = emotion_data['emotion']['fear']
                #
                ## Imprimir resultados
                #print(f"Emoción dominante: {dominant_emotion}")
                #print(f"Nivel de tristeza: {sadness_level}")
                #print(f"Nivel de miedo: {fear_level}")
                #print('hola mundo',type(analysis))

 
                emotion = analysis[0]['dominant_emotion']
                percentage = str(analysis[0]['emotion'][emotion])
                print('La emocion dominante fue: ',emotion, 'y su porcentaje fue: ',percentage)
                emotion_data.append(emotion)
                
                # Muestra el video con la emoción detectada
                cv2.putText(frame, f"Emocion: {emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.imshow("Video Analysis", frame)
            except Exception as e:
                print('')
                print(f"Error processing frame: {e}")
                cv2.destroyWindow()

            # Finaliza con tecla 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        #print('hola mundo')
        cap.release()
        cv2.destroyAllWindows()

    # Genera el reporte
    emotion_summary = Counter(emotion_data)
    emotion_df = pd.DataFrame(list(emotion_summary.items()), columns=["Emotion", "Count"])
    emotion_df.to_csv(output_csv, index=False)
    print("Report saved:", output_csv)

# Llama a la función para analizar video
analyze_video()

