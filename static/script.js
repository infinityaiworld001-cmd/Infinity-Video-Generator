const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const videoPlayer = document.getElementById("videoPlayer");
const downloadBtn = document.getElementById("downloadBtn");
const historyList = document.getElementById("historyList");
const placeholder = document.getElementById("placeholder");
const detectedEffect = document.getElementById("detectedEffect");

imageInput.addEventListener("change", function () {
    const file = imageInput.files[0];

    if (file) {
        previewImage.src = URL.createObjectURL(file);
        previewImage.style.display = "block";
    }
});

function generateVideo() {
    const file = imageInput.files[0];
    const prompt = document.getElementById("promptBox").value;
    const loading = document.getElementById("loading");

    if (!file) {
        alert("Please upload an image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);
    formData.append("prompt", prompt);

    loading.innerHTML = "Detecting image effect and generating video...";
    videoPlayer.style.display = "none";
    placeholder.style.display = "block";
    downloadBtn.style.display = "none";
    detectedEffect.innerHTML = "";

    fetch("/generate", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        loading.innerHTML = "Video generated successfully ✅";

        detectedEffect.innerHTML = "Detected Effect: " + data.effect.toUpperCase();

        videoPlayer.src = data.video_url + "?t=" + new Date().getTime();
        videoPlayer.style.display = "block";
        placeholder.style.display = "none";

        downloadBtn.href = data.video_url;
        downloadBtn.style.display = "inline-block";
        downloadBtn.innerHTML = "Download Video";

        loadHistory(data.history);
    })
    .catch(error => {
        loading.innerHTML = "Video generation failed";
        console.log(error);
    });
}

function loadHistory(history) {
    historyList.innerHTML = "";

    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";

        div.innerHTML = `
            <strong>${item.effect.toUpperCase()}</strong><br>
            <span>${item.prompt}</span>
        `;

        div.onclick = function () {
            videoPlayer.src = item.video + "?t=" + new Date().getTime();
            videoPlayer.style.display = "block";
            placeholder.style.display = "none";

            downloadBtn.href = item.video;
            downloadBtn.style.display = "inline-block";
            downloadBtn.innerHTML = "Download Video";

            detectedEffect.innerHTML = "Detected Effect: " + item.effect.toUpperCase();
        };

        historyList.appendChild(div);
    });
}