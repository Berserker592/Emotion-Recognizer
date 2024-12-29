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

