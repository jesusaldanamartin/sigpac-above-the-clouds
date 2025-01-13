// UPLOAD BOXES

const selectImages = document.querySelectorAll('.select-image');
const inputFiles = document.querySelectorAll('input[type="file"]');
const imgAreas = document.querySelectorAll('.img-area');

selectImages.forEach((button, index) => {
    const inputFile = inputFiles[index];
    const imgArea = imgAreas[index];

    button.addEventListener('click', function () {
        inputFile.click();
    });

    inputFile.addEventListener('change', function () {
        const image = this.files[0];
        if (image.size < 2000000000) {
            const reader = new FileReader();
            reader.onload = () => {
                const allImg = imgArea.querySelectorAll('img');
                allImg.forEach(item => item.remove());
                const imgUrl = reader.result;
                const img = document.createElement('img');
                img.src = imgUrl;
                imgArea.appendChild(img);
                imgArea.classList.add('active');
                imgArea.dataset.img = image.name;
            };
            reader.readAsDataURL(image);
        } else {
            alert("Image size more than 2GB");
        }
    });
});

// PROGRESS BAR

const button = document.getElementById('toggleButton'); // Access the button
const progress = document.querySelector('.progress'); // Access the progress bar
const h2 = document.querySelector('h2'); // Access the percentage text

let progressValue = 0; // Initialize progress value
let intervalId = null; // To hold the interval ID

button.addEventListener('click', () => {
    if (intervalId) {
        clearInterval(intervalId); // Clear any existing interval
    }

    intervalId = setInterval(() => {
        if (progressValue < 100) {
            progressValue++;
            updateProgress(progressValue);
        } else {
            clearInterval(intervalId); // Stop the interval when it reaches 100%
        }
    }, 30);
});

function updateProgress(value) {
    h2.textContent = value + '%'; // Update the percentage text
    progress.style.width = value + '%'; // Update the progress bar width
}

// UPLOAD
async function uploadFile(input, imgAreaId) {
    const form = input.closest("form");
    const formData = new FormData(form);
    const button = form.querySelector(".select-image");

    try {
        const response = await fetch(form.action, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (response.ok) {
            // Update the UI
            const imgArea = document.getElementById(imgAreaId);
            imgArea.innerHTML = `
                <div class="uploaded">
                    <i class="checkmark">&#10003;</i>
                    <p>File <strong>${data.filename}</strong> uploaded successfully!</p>
                </div>
            `;

            // Disable the button and file input to prevent further uploads
            button.disabled = true;
            input.disabled = true;
            button.textContent = "Uploaded"; // Change button text for clarity
            button.style.cursor = "not-allowed"; // Optionally change cursor style
            button.style.backgroundColor = "#4caf50"; // Green color for success
            button.style.color = "white"; // White text for contrast
            button.style.border = "none"; // Remove border if needed
        } else {
            alert(data.error || "File upload failed");
        }
    } catch (error) {
        console.error("Error uploading file:", error);
    }
}

document.getElementById('file1').addEventListener('change', function () {
    uploadFile(this, "img-area-1");
});

document.getElementById('file2').addEventListener('change', function () {
    uploadFile(this, "img-area-2");
});


// EXECUTION START BUTTOM

// document.getElementById('toggleButton').addEventListener('click', function() {
//     fetch('/start', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.error) {
//             alert(data.error);
//         } else {
//             alert(data.message || 'Process started successfully');
//             console.log('Processing Result:', data.result);
//         }
//     })
//     .catch(err => {
//         alert('An error occurred: ' + err.message);
//     });
// });


// RENDER MAP
document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.getElementById("toggleButton");
    const staticContainer = document.getElementById("static-container");
    const mapContainer = document.getElementById("map-container");

    startButton.addEventListener("click", () => {
        fetch('/execution', { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then(data => {
                if (data.png_url) {
                    // Hide static image and show map
                    staticContainer.style.display = "none";
                    mapContainer.style.display = "block";

                    // Initialize Leaflet map
                    const map = L.map('map').setView([0, 0], 2); // Adjust view as needed
                    L.imageOverlay(data.png_url, [[-90, -180], [90, 180]]).addTo(map);
                    map.fitBounds([[-90, -180], [90, 180]]);
                } else {
                    console.error("Failed to load processed image:", data.error);
                }
            })
            .catch(error => console.error("Error during execution:", error));
    });
});
