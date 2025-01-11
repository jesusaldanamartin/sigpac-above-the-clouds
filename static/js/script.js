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
        if (image.size < 2000000) {
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
            alert("Image size more than 2MB");
        }
    });
});

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
