let ws;
let isAnalyzing = true;
let mediaRecorder;
let recordedChunks = [];
let isRecording = false; // Estado para controlar la grabación

const emotionData = {};
const labels = [];
const emotionCounts = [];

const pauseButton = document.getElementById('toggle-btn');
const saveButton = document.getElementById('saveButton');
const startButton = document.getElementById('startanalisis');
const startButton2 = document.getElementById('startButton2');

const playButton = document.getElementById('videoUpload')
const playanButton = document.getElementById('analyzeVideoBtn')
const ReportsButton = document.getElementById('ReportsButton')

saveButton.disabled = true;
pauseButton.disabled = true;
ReportsButton.disabled = true;

saveButton.style.display = 'none'
pauseButton.style.display = 'none'
ReportsButton.style.display = 'none'
startButton2.style.display = 'none'

playButton.disabled = true;
playButton.style.display = 'none'


//Procesar video guardado

// Inicializar el gráfico cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
    
    const ctx = document.getElementById("emotionChart").getContext("2d");
    const scatterCtx = document.getElementById("emotionScatterChart").getContext("2d");
    const polarCtx = document.getElementById("emotionPolarChart").getContext("2d");
    //saveButton.disabled = true;
    //pauseButton.disabled = true;

    const scatterData = {
        datasets: [{
            label: "Emociones detectadas",
            data: [], // Aquí irán los puntos (x: emoción, y: porcentaje, r: tamaño del punto)
            backgroundColor: "rgba(54, 162, 235, 0.5)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
        }],
    };

    // Mapeo de emociones a valores en el eje Y
    const emotionMap = {
        Enojo: 7,
        Miedo: 6,
        Tristeza: 5,
        Neutral: 4,
        Desagrado: 3,
        Felicidad: 2,
        Sorpresa: 1,
        Desconocida:0
    };

    const labels = []; // Eje X: tiempo
    const emotionValues = []; // Valores en el eje Y según la emoción detectada
    const percentageValues = []


    const scatterOptions = {
        responsive: true,
        animation: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const emotionMap = {
                            0: "Desconocida",
                            1: "Sorpresa",
                            2: "Felicidad",
                            3: "Desagrado",
                            4: "Neutral",
                            5: "Tristeza",
                            6: "Miedo",
                            7: "Enojo"
                        };
                        const emotionLabel = emotionMap[context.raw.x] || "Desconocida";
                        return `Emoción: ${emotionLabel}, Porcentaje: ${context.raw.y}%, Personas: ${context.raw.r}`;
                    },
                },
            },
        },
        scales: {
            x: {
                title: { display: true, text: "Emoción" },
                ticks: {
                    callback: function(value) {
                        const emotionMap = {
                            0: "Desconocida",
                            1: "Sorpresa",
                            2: "Felicidad",
                            3: "Desagrado",
                            4: "Neutral",
                            5: "Tristeza",
                            6: "Miedo",
                            7: "Enojo"
                        };
                        return emotionMap[value] || "";
                    },
                    stepSize: 1,
                },
                min: 0,
                max: 7,
            },
            y: {
                title: { display: true, text: "Porcentaje (%)" },
                min: 0,
                max: 100,
            },
        },
    };

    const emotionScatterChart = new Chart(scatterCtx, {
        type: "scatter",
        data: scatterData,
        options: scatterOptions,
    });

    const emotionPolarChart = new Chart(polarCtx, {
        type: 'polarArea',
        data: {
            labels: [
                'Enojo',
                'Desagrado',
                'Miedo',
                'Felicidad',
                'Tristeza',
                'Sorpresa',
                'Neutral',
                
            ],
            datasets: [{
                label: 'Intensidad de emociones',
                data: [40, 20, 15, 25, 35, 18, 5], // // Datos iniciales (serán actualizados por WebSocket) Ejemplo de datos
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)', // Angry
                    'rgba(255, 159, 64, 0.5)', // Fear
                    'rgba(255, 205, 86, 0.5)', // Surprise
                    'rgba(75, 192, 192, 0.5)', // Excited
                    'rgba(54, 162, 235, 0.5)', // Happy
                    'rgba(153, 102, 255, 0.5)', // Relaxed
                    'rgba(201, 203, 207, 0.5)', // Sleepy
                    //'rgba(100, 123, 150, 0.5)', // Tired
                    //'rgba(160, 82, 45, 0.5)', // Bored
                    //'rgba(120, 45, 78, 0.5)', // Depressed
                    //'rgba(220, 20, 60, 0.5)', // Sad
                    //'rgba(189, 183, 107, 0.5)', // Disgust
                    //'rgba(255, 255, 255, 0.5)' // Neutral
                ]
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    ticks: { display: false }, // Ocultar etiquetas de escala
                }
            },
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });    

    // Actualización dinámica del gráfico polar
    function updatePolarChart(emotion) {
        emotionPolarChart.data.datasets[0].data = emotion;
        emotionPolarChart.update();
    }

    // Simular datos dinámicos desde el WebSocket
    //setInterval(() => {
    //    const simulatedData = Array.from({ length: 7 }, () => Math.floor(Math.random() * 100));
    //    updatePolarChart(simulatedData);
    //}, 5000); // Actualiza cada 5 segundos

    const emotionChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
            {
                label: "Emoción detectada",
                data: emotionValues,
                borderColor: "rgb(75, 192, 192)",
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderWidth: 2,
                tension: 0.4, // Suavizar la línea para una apariencia continua
            },
            {
                label: "Porcentaje de detección",
                data: percentageValues,
                borderColor: "rgb(255, 159, 64)",
                backgroundColor: "rgba(255, 159, 64, 0.2)",
                tension: 0.4,
                borderWidth: 2,
                yAxisID: 'y1', // Usar el segundo eje Y para el porcentaje
            },
        ],
        },
        options: {
            responsive: true,
            animation: false,
            scales: {
                x: {
                    title: { display: true, text: "Tiempo (s)" },
                },
                y: {
                    title: { display: true, text: "Emoción" },
                    ticks: {
                        callback: function(value) {
                            // Mostrar etiquetas de emociones en el eje Y
                            return Object.keys(emotionMap).find(key => emotionMap[key] === value);
                        },
                        stepSize: 1, // Asegurar que cada emoción esté representada
                    },
                    min: 0,
                    max: 7,
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: "Porcentaje (%)" },
                    ticks: {
                        min:0,
                        max: 100,
                        stepSize:10
                    },
                    grid: {
                        drawOnChartArea: false, // No dibujar la cuadrícula para el eje de porcentaje              

                    },
                },        
            },
        },
    });



 


    // Actualizar datos del gráfico de dispersión
    function updateScatterChart(emotion, percentage, personsDetected) {
        const emotionMap = {
            Enojo: 7,
            Miedo: 6,
            Tristeza: 5,
            Neutral: 4,
            Desagrado: 3,
            Felicidad: 2,
            Sorpresa: 1,
            Desconocida: 0,
        };

        const emotionValue = emotionMap[emotion] ?? null;
        if (emotionValue !== null) {
            emotionScatterChart.data.datasets[0].data.push({
                x: emotionValue,
                y: percentage,
                r: personsDetected ? personsDetected * 2 : 5, // Tamaño del punto
            });

            //if (emotionScatterChart.data.datasets[0].data.length > 30) {
            //    emotionScatterChart.data.datasets[0].data.shift(); // Limitar la cantidad de puntos
            //}

            emotionScatterChart.update();
        }
    }


    function updateChart(emotion, timestamp, percentage) {
        if (!labels.includes(timestamp)) {
            labels.push(timestamp);
            if (labels.length > 30) labels.shift(); // Mantener máximo 30 puntos en el gráfico
        }

        const emotionValue = emotionMap[emotion] ?? null;
        if (emotionValue !== null) {
            emotionValues.push(emotionValue);
            if (emotionValues.length > 30) emotionValues.shift(); // Limitar la longitud del dataset
        }
        if (percentage !== null) {
            percentageValues.push(percentage);
            if (percentageValues.length > 30) percentageValues.shift(); // Limitar la longitud del dataset para el porcentaje
        }
        emotionChart.update();
    }

    function startWebSocket() {
        ws = new WebSocket("ws://127.0.0.1:8000/ws");
        
        ws.onmessage = event => {
            const data = JSON.parse(event.data);
            if (data.emotion) {
                document.querySelector("#emotion").innerText = "Emoción detectada: " + data.emotion + " ==> Porcentaje: " + data.percentage;

                if (data.percentage) {
                    document.querySelector("#percentage").innerText = "Porcentaje: " + data.percentage;
                }

                if (data.NumeroPersonas) {
                    document.querySelector("#NumeroPersonas").innerText = "Personas Detectadas: " + data.NumeroPersonas;
                }

                if (data.Tiempo) {
                    document.querySelector("#endan").innerText = "Tiempo Transcurrido: " + data.Tiempo;
                }

                const currentTime = new Date().toLocaleTimeString();
                updateChart(data.emotion, currentTime, data.percentage, data.NumeroPersonas);
                updateScatterChart(data.emotion, data.percentage, data.NumeroPersonas);
                updatePolarChart(data.emociones);
                
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
    pauseButton.disabled = false;
    saveButton.disabled = false;
    
    startButton.disabled = true;
    startButton.style.display = 'none'
    startButton2.style.display = 'none'
    playanButton.style.display = "none";
    pauseButton.style.display = 'block';
    saveButton.style.display = 'block';
    ReportsButton.style.display = 'block';


    const placeholder = document.getElementById("placeholder");
    //const video1 = document.getElementById("video");

    // Ocultar la imagen y mostrar el video
    placeholder.style.display = "none";
    video.style.display = "block";

    // Aquí puedes agregar lógica para iniciar la grabación
    console.log("Grabación iniciada");


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
        }, 200); // Enviar frames cada 200ms
    });
}

function playStream(){
    const videoUpload = document.getElementById("videoUpload");
    const uploadedVideo = document.getElementById("uploadedVideo");
    const videoCanvas = document.createElement("canvas"); // Canvas para extraer fotogramas
    const ctx = videoCanvas.getContext("2d");

    startButton.style.display = 'none'
    playButton.style.display = 'block'
    playButton.disabled = false
    //pauseButton.disabled = false
    //saveButton.disabled = false

    const placeholder = document.getElementById("placeholder");
    //const video1 = document.getElementById("video");

    // Ocultar la imagen y mostrar el video
    placeholder.style.display = "none";
    uploadedVideo.style.display = "block";

    // Detectar cuando se carga un video
    console.log("Video Cargando");
    videoUpload.addEventListener("change", async (event) => {
        console.log("Video Subido");
        
        const file = event.target.files[0];
        if (!file) return;

        // Cargar el video en el elemento de reproducción
        const videoURL = URL.createObjectURL(file);
        uploadedVideo.src = videoURL;

        // Procesar el video fotograma por fotograma
        uploadedVideo.addEventListener("play", () => {
            const interval = setInterval(async () => {
                if (uploadedVideo.paused || uploadedVideo.ended) {
                    clearInterval(interval);
                    return;
                }

                // Dibujar el fotograma actual en el canvas
                videoCanvas.width = uploadedVideo.videoWidth;
                videoCanvas.height = uploadedVideo.videoHeight;
                ctx.drawImage(uploadedVideo, 0, 0, videoCanvas.width, videoCanvas.height);

                // Convertir el fotograma en base64
                const frame = videoCanvas.toDataURL("image/jpeg");
                console.log("Procesando");
                ws.send(frame);


                // Enviar el fotograma al backend para análisis
                //const response = await fetch("/ws", {
                //    method: "POST",
                //    headers: { "Content-Type": "application/json" },
                //    body: JSON.stringify({ frame })
                //});
//
                //const result = await response.json();
                //console.log(result); // Mostrar los resultados en la consola
                // Aquí puedes actualizar gráficos o la UI con los resultados
            }, 200); // Procesar cada 100ms
        });
    });
}

// Alternar análisis sin detener grabación
function toggleAnalysis() {
    isAnalyzing = !isAnalyzing;
    document.querySelector("#toggle-btn").innerText = isAnalyzing ? "Pausar" : "Reanudar";
    saveButton.disabled = false;
    
    const placeholder = document.getElementById("placeholder");
    const video = document.getElementById("video");



    // Aquí puedes agregar lógica para detener la grabación
    console.log("Grabación detenida");

    if (isAnalyzing && !isRecording) {
        // Si el análisis se reanuda, reanudar la grabación si estaba detenida
        //mediaRecorder.start();
        
        // Mostrar la imagen y ocultar el video
        placeholder.style.display = "none";
        video.style.display = "block";
        isRecording = true;
        console.log("Grabación reanudada");
    } else if (!isAnalyzing && isRecording) {
        // Si el análisis se pausa, detener la grabación
        mediaRecorder.stop();
        isRecording = false;
        // Mostrar la imagen y ocultar el video
        placeholder.style.display = "block";
        video.style.display = "none";
        //pauseButton.disabled = true;
        //pauseButton.style.display = 'none'
        console.log("Grabación pausada");
    
        // Detener el flujo de la cámara (apagarla)
        const stream = video.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        video.srcObject = null; // Detener el video
        
    }

}

// Detener grabación y enviar datos
function stopRecording() {
    startButton.disabled = false
    
    if (mediaRecorder && mediaRecorder.state === "recording") {
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
                recordedChunks = [];
            });
    startButton.style.display = 'none'
    startButton2.style.display = 'block'   
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

