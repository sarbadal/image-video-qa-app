var zoomSlider = document.getElementById("zoomRange");
var zoomOutput = document.getElementById("zoom");
zoomOutput.innerHTML = 'Zoom Index: ' + zoomSlider.value; // Display the default slider value

var thresholdSlider = document.getElementById("thresholdRange");
var thresholdOutput = document.getElementById("threshold");
thresholdOutput.innerHTML = 'Size Threshold: ' + thresholdSlider.value; // Display the default slider value

var redSlider = document.getElementById("redRange");
var greenSlider = document.getElementById("greenRange");
var blueSlider = document.getElementById("blueRange");
var colorOutput = document.getElementById("rgbColor");
let rgbValue = redSlider.value + ', ' + greenSlider.value + ', ' + blueSlider.value;
colorOutput.innerHTML = 'Color RGB: [' + rgbValue + ']'

// Update the current slider value (each time you drag the slider handle)
zoomSlider.oninput = function() {
    zoomOutput.innerHTML = 'Zoom Index: ' + this.value;
}

thresholdSlider.oninput = function() {
    thresholdOutput.innerHTML = 'Size Threshold: ' + this.value;
}

redSlider.oninput = function() {
    colorOutput.innerHTML = 'Color RGB: [' + redSlider.value + ', ' + greenSlider.value + ', ' + blueSlider.value + ']';
}

greenSlider.oninput = function() {
    colorOutput.innerHTML = 'Color RGB: [' + redSlider.value + ', ' + greenSlider.value + ', ' + blueSlider.value + ']';
}

blueSlider.oninput = function() {
    colorOutput.innerHTML = 'Color RGB: [' + redSlider.value + ', ' + greenSlider.value + ', ' + blueSlider.value + ']';
}
