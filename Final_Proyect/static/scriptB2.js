let ws;
let isAnalyzing = true;
let mediaRecorder;
let recordedChunks = [];
let isRecording = false; // Estado para controlar la grabación

const emotionData = {};
const labels = [];
const emotionCounts = [];

// Inicializar el gráfico cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById("emotionChart").getContext("2d");
    const emotionChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Frecuencia de emociones detectadas",
                data: emotionCounts,
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderColor: "rgb(75, 192, 93)",
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

    // Inicializar WebSocket y manejar mensajes
    function startWebSocket() {
        ws = new WebSocket("ws://127.0.0.1:8000/ws");
        ws.onmessage = event => {
            const data = JSON.parse(event.data);
            if (data.emotion) {
                document.querySelector("#emotion").innerText = "Emoción detectada: " + data.emotion;
                updateChart(data.emotion);
            }
        };
        ws.onclose = () => console.error("WebSocket cerrado. Intenta reconectarte.");
        ws.onerror = error => console.error("Error en WebSocket:", error);
    }

    startWebSocket();
});

// Función para iniciar la transmisión de video y análisis
function startStream() {
    const video = document.querySelector("#video");
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(stream => {
        video.srcObject = stream;
        video.play();

        // Configuración de grabación
        mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });
        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        // Iniciar grabación
        mediaRecorder.start();
        isRecording = true;
        console.log("Grabación iniciada");

        // Procesamiento de video para análisis
        setInterval(() => {
            if (isAnalyzing) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                const frame = canvas.toDataURL("image/jpeg");
                ws.send(frame);
            }
        }, 2000); // Enviar frames cada 200ms
    });
}

// Alternar análisis sin detener grabación
function toggleAnalysis() {
    isAnalyzing = !isAnalyzing;
    document.querySelector("#toggle-btn").innerText = isAnalyzing ? "Pausar" : "Reanudar";
}

// Detener grabación y enviar datos
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
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
                recordedChunks = [];
            });
    }
}

// Obtener reportes desde el servidor
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
