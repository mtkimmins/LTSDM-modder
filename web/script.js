//////////////////////////////////////////
//      CONSTANTS
//////////////////////////////////////////

//taskbar stuff
const topTaskbar = document.getElementById("top-taskbar");
const compileLTSDMButton = document.getElementById("compile-ltsdm-button");
const compileSVGButton = document.getElementById("compile-svg-button");
const compilePDFButton = document.getElementById("compile-pdf-button");

//data stuff
const dataContainer = document.getElementById("data-container");
const frame = document.getElementById("frame");

//audio stuff
const uploadAudioButton = document.getElementById("audio-upload-button");
const audioInput = document.getElementById("audio-input");

//image stuff

//summary bar stuff

//////////////////////////////////////////
//      VARIABLES
/////////////////////////////////////////
let image_lock = false;
let frame_elements = [];


///////////////////////////////////////////
//      EVENT LISTENERS
///////////////////////////////////////////
//compiling
function compileLTSDM(){};
function compileSVG(){};
function compilePDF(){};
function compileFull(){};
function setCompileLocation(){};

//adding and managing audio files
function uploadAudio(){};
function processAudio(){};

function resetAudio(){};

function playAudio(){};
function resumeAudio(){};
function stopAudio(){};

//managing light data
function selectLightInterval(){};
function moveLightIndicator(){};

function dragProgressBar(){};

function cutAudioSegment(){};
function jumpTime(){};
function assignLightColour(){};

//managing image data
function uploadImage(){};
function toggleImageEdits(){
    image_lock = !image_lock;
};


///////////////////////////////////////////
//      CREATION
///////////////////////////////////////////
//VERIFIED
function generateFrameElements() {
    if (frame_elements.length == 0) {
        frame_elements.push(frame);
    };
    while (frame_elements.length < 12) {
        // Clone the frame element and append it to the array
        let nextFrame = frame.cloneNode(true);
        nextFrame.id = "frame" + (frame_elements.length + 1);
        nextFrame.querySelector(".frame-number").textContent = frame_elements.length + 1;
        frame_elements.push(nextFrame);
    }
    console.log("Generated frame elements:", frame_elements);
}
//VERIFIED
function addFrameElements() {
    //check what frames are already children of the data container
    for (let i = 0; i < frame_elements.length; i++) {
        if (!dataContainer.contains(frame_elements[i])) {
            dataContainer.appendChild(frame_elements[i]);
        }
    }
};

function initializeLTSDMElements() {};

////////////////////////////////////////////
//      RUNTIME
////////////////////////////////////////////
//Populate the frame elements
generateFrameElements();
addFrameElements();

//list of frames
frame_elements.forEach((frame) => {
    let uploadButton = frame.querySelector(".audio-upload-button");
    let audioInput = frame.querySelector(".audio-input");
    let fileName = frame.querySelector(".file-name");
    let format = frame.querySelector(".format");
    let ogSize = frame.querySelector(".og-size");
    let length = frame.querySelector(".length");
    
    // trigger the upload input when the button is clicked
    uploadButton.addEventListener("click", () => {
        audioInput.click();
    });

    // display the selected file name when a file is chosen
    audioInput.addEventListener("change", () => {
        if (audioInput.files.length > 0) {
            fileName.textContent = audioInput.files[0].name;
            format.textContent = audioInput.files[0].name.split('.').pop().toUpperCase();
            ogSize.textContent = audioInput.files[0].size;
            
            let audioElement = document.createElement("audio");
            audioElement.src = URL.createObjectURL(audioInput.files[0]);
            audioElement.addEventListener("loadedmetadata", () => {
                let duration = audioElement.duration;
                let durationMinutes = Math.floor(duration/60);
                let durationSeconds = Math.floor(duration % 60);
                let durationFormatted = durationMinutes.toString().padStart(2, '0') + ":" + durationSeconds.toString().padStart(2, '0');
                length.textContent = durationFormatted;
                audioElement.remove(); // Clean up the audio element after getting the duration
            });
        }
    });
});