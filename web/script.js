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
        nextFrame.querySelector("#frame-number").textContent = frame_elements.length + 1;

        // label all children of the frame with their name + their frame number
        const children = nextFrame.querySelectorAll("*");
        children.forEach(child => {
            if (child.id) {
                child.id = child.id + "-" + (frame_elements.length + 1);
            }
        });
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