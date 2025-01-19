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
let pausePoints = [14, 76]; // Define points where the progress bar will pause
let isPaused = false; // Track if the progress is currently paused

button.addEventListener('click', () => {
    if (intervalId) {
        clearInterval(intervalId); // Clear any existing interval
    }

    progressValue = 0; // Reset progress value
    isPaused = false; // Reset pause state
    updateProgress(progressValue); // Reset progress visuals

    intervalId = setInterval(() => {
        if (!isPaused) { // Only proceed if not paused
            if (progressValue < 100) {
                progressValue++;
                updateProgress(progressValue);

                if (pausePoints.includes(progressValue)) {
                    isPaused = true; // Pause at the specified point
                    setTimeout(() => {
                        isPaused = false; // Resume after a delay
                    }, 3000); // 5-second pause
                }
            } else {
                clearInterval(intervalId); // Stop the interval when it reaches 100%
            }
        }
    }, 175); // Delay
});


function populateMetricsTable(metrics) {
    const container = document.getElementById('metrics-table-container');

    // Clear any existing content
    container.innerHTML = '';

    // Create table
    const table = document.createElement('table');
    table.className = 'metrics-table';

    // Add headers
    const headerRow = document.createElement('tr');
        const headers = ['Category', 'Aciertos', 'Fallos', 'Porcentaje de acierto', 'Num Pixeles'];
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Add rows
    metrics.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });

    container.appendChild(table);
}

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

document.addEventListener("DOMContentLoaded", () => {
    const metricsToggleButton = document.getElementById("btn-metrics-toggle"); // Toggle button for metrics table
    const metricsTableContainer = document.getElementById("metrics-table-container"); // Metrics table container
    const staticContainer = document.getElementById("static-container"); // Upload forms container
    const mapContainer = document.getElementById("map-container"); // Map container
    let currentMap = null; // Store the current map instance

    const mapButtons = {
        classification: document.getElementById("btn-classification"),
        trueFalse: document.getElementById("btn-true-false"),
        confMatrix: document.getElementById("btn-conf-matrix"),
    };

    // Toggle metrics table visibility
    metricsToggleButton.addEventListener("click", () => {
        const isTableVisible = metricsTableContainer.style.display !== 'none';

        if (isTableVisible) {
            metricsTableContainer.style.display = 'none'; // Hide metrics table
            staticContainer.style.display = 'block'; // Show the upload forms and progress bar
        } else {
            metricsTableContainer.style.display = 'block'; // Show metrics table
            staticContainer.style.display = 'none'; // Hide the upload forms and progress bar
        }
    });

    // Function to render the metrics table
    function renderMetricsTable(metrics) {
        const table = document.createElement("table");
        table.className = "metrics-table";

        // Add table headers
        const headerRow = table.insertRow();
        ["Metric", "Value", "Details"].forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });

        // Add table rows
        metrics.forEach(metric => {
            const row = table.insertRow();
            Object.values(metric).forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value;
            });
        });

        // Clear the container and append the new table
        metricsTableContainer.innerHTML = "";
        metricsTableContainer.appendChild(table);
    }

    // Fetch and handle the execution response
    const startButton = document.getElementById("toggleButton");
    startButton.addEventListener("click", () => {
        fetch('/execution', { method: 'POST' })
            console.log(response)
            .then(response => response.json())
            .then(data => {
                if (data.metrics_table) {
                    // Hide upload boxes and progress bar
                    document.getElementById('container-group').style.display = 'none';
                    document.getElementById('container-buttom').style.display = 'none';

                    // Populate and show the metrics table
                    renderMetricsTable(data.metrics_table);
                    metricsTableContainer.style.display = 'block';
                } else {
                    console.error("Failed:", data.error);
                }
            })
            .catch(error => console.error("Error during execution:", error));
    });

    // Function to display an image on the map
    function displayImage(imageUrl) {
        staticContainer.style.display = "none"; // Hide static container
        mapContainer.style.display = "block"; // Show map container

        if (currentMap) {
            currentMap.remove(); // Destroy the existing map
        }

        currentMap = L.map('map').setView([0, 0], 4); // Set default view
        L.imageOverlay(imageUrl, [[-90, -180], [90, 180]]).addTo(currentMap);
        currentMap.fitBounds([[-90, -180], [90, 180]]);
    }

    // Event listeners for map buttons
    mapButtons.classification.addEventListener("click", () => {
        displayImage('/output/styled_sigpac_file.png');
    });

    mapButtons.trueFalse.addEventListener("click", () => {
        displayImage('/output/styled_red_green.png');
    });

    mapButtons.confMatrix.addEventListener("click", () => {
        displayImage('/output/styled_conf_matrix.png');
    });

    // Render example metrics on page load (optional)
    const exampleMetrics = [
        { Metric: "Accuracy", Value: "95%", Details: "Model's accuracy in classification tasks" },
        { Metric: "Precision", Value: "93%", Details: "Precision of cropland classification" },
        { Metric: "Recall", Value: "94%", Details: "Recall for land cover prediction" }
    ];
    renderMetricsTable(exampleMetrics);
});


document.getElementById("btn-metrics-toggle").addEventListener("click", function () {
    const uploadContainer = document.getElementById("bottom-left-container");
    const metricsTableContainer = document.getElementById("metrics-table-container");

    // Swap visibility of the upload container and metrics table
    if (uploadContainer.style.display === "none") {
        uploadContainer.style.display = "flex"; // Show upload boxes and progress bar
        metricsTableContainer.style.display = "none"; // Hide metrics table
    } else {
        uploadContainer.style.display = "none"; // Hide upload boxes and progress bar
        metricsTableContainer.style.display = "block"; // Show metrics table
    }
});

// Sample function to render a metrics table dynamically from JSON
function renderMetricsTable(metrics) {
    const metricsTableContainer = document.getElementById("metrics-table-container");

    // Clear previous table content
    metricsTableContainer.innerHTML = "";

    // Create table element
    const table = document.createElement("table");
    table.classList.add("metrics-table");

    // Add headers
    const headers = ['Category', 'Aciertos', 'Fallos', 'Porcentaje de acierto', 'Num Pixeles'];
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headers.forEach(header => {
        const th = document.createElement("th");
        th.textContent = header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Add rows from JSON data
    const tbody = document.createElement("tbody");
    metrics.forEach(row => {
        const tr = document.createElement("tr");

        Object.values(row).forEach(value => {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    // Append table to container
    metricsTableContainer.appendChild(table);
}