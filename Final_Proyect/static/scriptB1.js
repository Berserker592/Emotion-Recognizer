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
    
    // Iniciar acceso a la cámara
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
        
        // Procesamiento del video para análisis
        setInterval(() => {
            if (isAnalyzing) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                const frame = canvas.toDataURL("image/jpeg");
                ws.send(frame);
            }
        }, 2000);// Envía frames cada 200ms
    });

    ws.onmessage = event => {
        const data = JSON.parse(event.data);

        //const datos1 = data.datos1;
        //const datos2 = data.datos2;

        //document.querySelector("#person_detect").innerText = "Persona detectada: " + data.value;
        document.querySelector("#emotion").innerText = "Emoción detectada: " + data.emotion;
            
    };
}


// Alternar análisis sin detener la grabación
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


// Guardar la grabación al final
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
            //recordedChunks = [];
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



const emotionData = {};
const labels = [];
const emotionCounts = [];
// Inicializar el gráfico
const ctx = document.getElementById("emotionChart").getContext("2d");
const emotionChart = new Chart(ctx, {
    type: "bar",
    data: {
        labels: labels,
        datasets: [{
            label: "Frecuencia de emociones detectadas",
            data: emotionCounts,
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 1,
        }],
    },
    options: {
        scales: {
            y: { beginAtZero: true },
        },
    },
});
function updateChart(emotion) {
    if (!emotionData[emotion]) {
        emotionData[emotion] = 0;
        labels.push(emotion);
        emotionCounts.push(0);
    }
    emotionData[emotion] += 1;
    const index = labels.indexOf(emotion);
    emotionCounts[index] = emotionData[emotion];
    emotionChart.update();
}
ws.onmessage = event => {
    const data = JSON.parse(event.data);
    document.querySelector("#emotion").innerText = "Emoción detectada: " + data.emotion;
    updateChart(data.emotion);
};

