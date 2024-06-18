/* ######################################################
########################PHASE2########################
###################################################### */
const canvas = document.getElementById('canvas');
const video = document.getElementById('video');
const context = canvas.getContext('2d');
const captureButton = document.getElementById('captureButton');
const segmentationTypeSelect = document.getElementById('segmentationType');
const maskColorInput = document.getElementById('maskColor');
const loading = document.getElementById('loading');
const imageTypeSelect = document.getElementById('imageType');
const uploadInput = document.getElementById('uploadInput');
const downloadButton = document.getElementById('downloadButton');

let segmentedImgUrl = '';

function startWebcam() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            console.error('Error accessing webcam: ', err);
        });
}

function stopWebcam() {
    let stream = video.srcObject;
    let tracks = stream.getTracks();

    tracks.forEach(function(track) {
        track.stop();
    });

    video.srcObject = null;
}

function updateUI() {
    if (imageTypeSelect.value === 'upload') {
        captureButton.style.display = 'none';
        uploadInput.style.display = 'block';
        video.style.display = 'none';
        downloadButton.style.display = 'none';
        stopWebcam();
    } else if (imageTypeSelect.value === 'webcam' && segmentationTypeSelect.value === 'hair') {
        captureButton.style.display = 'none';
        uploadInput.style.display = 'none';
        video.style.display = 'block';
        downloadButton.style.display = 'none';
        startWebcam();
        sendFrame();
    } else {
        captureButton.style.display = 'block';
        uploadInput.style.display = 'none';
        video.style.display = 'block';
        downloadButton.style.display = 'none';
        startWebcam();
    }
}

let animationFrameId;

async function sendFrame() {
    if (segmentationTypeSelect.value === 'hair' && imageTypeSelect.value === 'webcam') {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataUrl = canvas.toDataURL('image/png');
        const maskColor = maskColorInput.value;
        const segmentationType = segmentationTypeSelect.value;

        const response = await fetch('/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'image_data=' + encodeURIComponent(imageDataUrl) + '&mask_color=' + encodeURIComponent(maskColor) + '&segmentation_type=' + encodeURIComponent(segmentationType)
        });

        if (response.ok) {
            const result = await response.json();
            const segmentedImg = new Image();
            segmentedImg.onload = function () {
                context.drawImage(segmentedImg, 0, 0, canvas.width, canvas.height);
            };
            segmentedImg.src = 'data:image/png;base64,' + result.segmented_image;
            segmentedImgUrl = segmentedImg.src;
        } else {
            console.error('Error processing the frame');
        }

        animationFrameId = requestAnimationFrame(sendFrame);
    }
}

captureButton.addEventListener('click', async () => {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageDataUrl = canvas.toDataURL('image/png');
    const maskColor = maskColorInput.value;
    const segmentationType = segmentationTypeSelect.value;

    loading.style.display = 'block';

    const response = await fetch('/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'image_data=' + encodeURIComponent(imageDataUrl) + '&mask_color=' + encodeURIComponent(maskColor) + '&segmentation_type=' + encodeURIComponent(segmentationType)
    });

    if (response.ok) {
        const result = await response.json();
        const segmentedImg = new Image();
        segmentedImg.onload = function () {
            context.drawImage(segmentedImg, 0, 0, canvas.width, canvas.height);
            loading.style.display = 'none';
            downloadButton.style.display = 'block';
        };
        segmentedImg.src = 'data:image/png;base64,' + result.segmented_image;
        segmentedImgUrl = segmentedImg.src;
    } else {
        console.error('Error processing the frame');
        loading.style.display = 'none';
    }
});

imageTypeSelect.addEventListener('change', updateUI);
segmentationTypeSelect.addEventListener('change', updateUI);

uploadInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = async function (e) {
            const image = new Image();
            image.onload = async function () {
                canvas.width = image.width;
                canvas.height = image.height;
                context.drawImage(image, 0, 0);

                const imageDataUrl = canvas.toDataURL('image/png');
                const maskColor = maskColorInput.value;
                const segmentationType = segmentationTypeSelect.value;

                loading.style.display = 'block';

                const response = await fetch('/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'image_data=' + encodeURIComponent(imageDataUrl) + '&mask_color=' + encodeURIComponent(maskColor) + '&segmentation_type=' + encodeURIComponent(segmentationType)
                });

                if (response.ok) {
                    const result = await response.json();
                    const segmentedImg = new Image();
                    segmentedImg.onload = function () {
                        context.drawImage(segmentedImg, 0, 0, canvas.width, canvas.height);
                        loading.style.display = 'none';
                        downloadButton.style.display = 'block';
                    };
                    segmentedImg.src = 'data:image/png;base64,' + result.segmented_image;
                    segmentedImgUrl = segmentedImg.src;
                } else {
                    console.error('Error processing the frame');
                    loading.style.display = 'none';
                }
            };
            image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

downloadButton.addEventListener('click', () => {
    const link = document.createElement('a');
    link.href = segmentedImgUrl;
    link.download = 'segmented_image.png';
    link.click();
});

updateUI();
/* ######################################################
########################PHASE2########################
###################################################### */