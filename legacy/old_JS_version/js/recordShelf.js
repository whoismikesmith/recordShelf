var socket = new WebSocket('ws://recordshelf.local:7890');

var numRecordLEDs = 20 * 12;
var totalRecords = 794;
var divFactor = totalRecords/numRecordLEDs;
var numLEDs = 320;
var ledArr = Array.apply(0, Array(numLEDs)).map(function (x, y) { //numBoxes = 16
		return y + 1; 
		});  // [1, 2, 3]
var numBoxes = 16;
var pixelsPerBox = numLEDs/numBoxes;
var numLEDbytes = numLEDs * 3;
var packet = new Uint8ClampedArray(4 + numLEDbytes);
var completeBox = null;
var count = 0;
var selectedArray = [];
var modifiedArray = [];
var deletedArray = [];
var onOrOff = "Off";
var startSpeed = 200;
var duration = 3000;
var run;	 
var rando;
var boxno = 1;
var pixelno;
var bc = 1;
var frameno = 1;
var pos = 1;
var brightness = 255;
var timer = null;
var timer2 = null;
var timer3 = null;
var timer4 = null;
var timer5 = null;
var timer6 = null;
var timer7 = null;
var currentEffectName = null;
//colorpick
var activeR = null;
var activeG = null;
var activeB = null;
//colorpick2
var activeR2 = null;
var activeG2 = null;
var activeB2 = null;
var frames = [];
var mouseMove = null;
var mouseMoveTime = 5 * 1000 // 5 seconds. resets pixels when mouse doesn't move
var popLabel = null
var mostPopularLabels = [];
var mostPopularArtists = [];
// Animation parameters
        var lastTime = 0;
        var phase = 0;





function mode(array)
{
    if(array.length == 0)
    	return null;
    var modeMap = {}; // array of occurence counts
    var topTen = {}; //array of most common occurence
    var maxEl = array[0], maxCount = 1;
    for(var i = 0; i < array.length; i++)
    {
    	var el = array[i]; //el is single item within array
    	if(modeMap[el] == null) //if never seen this el before
    		modeMap[el] = 1; 	//set occurence count to 1
    	else
    		modeMap[el]++;		//increase that items occurence count
    	if(modeMap[el] > maxCount) //new most occuring, do this
    	{
    		maxEl = el;		//most popular el
    		maxCount = modeMap[el]; //set maxCount to most popular el's count
    		if (modeMap[el] > 5) { //if occured more than 5 times
    		topTen[el] = el+" "+modeMap[el];
    		}
    	}
    	
    }
    //return maxCount+" "+maxEl+" records.";
    var result = "Result : "+topTen.length;
   
    return result;
};


var getRandomInt = function(min, max) {
	return Math.floor(Math.random() * max) + min  
};

//create the master box array that mimics the dimensions of my Expedit shelf
var box = Array.apply(0, Array(numBoxes)).map(function (x, y) { //numBoxes = 16
		return y + 1; 
		});  // [1, 2, 3]
	box.forEach(function(pixel){
		box[pixel] = Array.apply(0, Array(pixelsPerBox)).map(function (x, y) { //numLEDs/numBoxes = 20 (pixelsPerBox)
			var result = y + 1 + (20 * count); 
			return result;  
		});  // [1, 2, 3]
		count++;
	});

//convers #FF0000 to [255,0,0]
var convertHex = function(hex){
	hex = hex.replace('#','');
	r = parseInt(hex.substring(0,2), 16);
	g = parseInt(hex.substring(2,4), 16);
	b = parseInt(hex.substring(4,6), 16);
	
	var result= [];
	result[0] = r;
	result[1] = g;
	result[2] = b;
	return result;
};


var writeModArray = function(r,g,b){
	writePixels( multiPixel(modifiedArray,r,g,b));
};
		  	
var trueBlack = function(){
		for (i=0; i<packet.length; i++){
			packet[i] = 0;
		}
		return packet;
	};
			
			var blinkMulti = function(count, speed){
				var delayStart = 100;
				for (i=0; i<count; i++){
					setTimeout(function(){
						writeModArray(activeR2,activeG2,activeB2) }, delayStart);
					setTimeout(function(){
						writeModArray(0,0,0) }, delayStart + speed);
					delayStart = delayStart + (2*speed);
					setTimeout(function(){
						writeModArray(activeR2,activeG2,activeB2) }, delayStart);

					
				};
									
			};
			
			var blinkSingle = function(count, speed){
				var delayStart = 100;
				for (i=0; i<count; i++){
					setTimeout(function(){
						writeModArray(activeR2,activeG2,activeB2) }, delayStart);
					setTimeout(function(){
						writeModArray(0,0,0) }, delayStart + speed);
					delayStart = delayStart + (2*speed);
					setTimeout(function(){
						writeModArray(activeR2,activeG2,activeB2) }, delayStart);
	
					
				};
									
			};
			
			var blinkBox = function(count, speed){
				var delayStart = 100;
				for (i=0; i<count; i++){
					setTimeout(function(){
						writePixels(simpleSingleBox(modifiedArray[0],activeR,activeG,activeB)) }, delayStart);
					setTimeout(function(){
						writePixels(simpleSingleBox(modifiedArray[0],0,0,0)); }, delayStart + speed);
					delayStart = delayStart + (2*speed);
					setTimeout(function(){
						writePixels(simpleSingleBox(modifiedArray[0],activeR,activeG,activeB)); }, delayStart);
	
					
				};
									
			};



function singleColorFrame(r, g, b) {
            /*
             * Create a full frame by repeating a single color
             */
//alert(chosen); 
	//console.log(chosen); et below
    var leds = numLEDs;
    
    // Dest position in our packet. Start right after the header.
    var dest = 1; //at some point had to change this from 4 to 1 to keep it working
    
    // Chosen pixel gets RGB values, all others get 0
    for (var led = 1; led <= leds; led++) {
			
		    	//console.log("pixel match found : "+led)
		    	dest = (led*3); //move to correct position
	    		packet[dest++] = r;
	        	packet[dest++] = g;
	        	packet[dest++] = b;
	    	
	   
    } // end for
    return packet;

        }

var blackness = singleColorFrame(0,0,0);

function writeBlackFrame (){
	console.log("writeBlackFrame() called");
	writePixels(blackness);
	
};
function simpleSingleBox (ledSelect, r, g, b){
	var chosen = parseInt(ledSelect);
	console.log ("Chosen : " + chosen);
	count = 0;
	
	box.forEach(function(pixel){
		if (box[pixel].indexOf(chosen) != -1){
		box[pixel].forEach(function(){
			completeBox = box[pixel];
		})
		}
		
		count++;
	});
	
	console.log(completeBox);
	dest = 1+(completeBox[0] * 3);
	completeBox.forEach(function(){
		packet[dest++] = r;
		packet[dest++] = g;
		packet[dest++] = b;
	});
	return packet;
};

		
		//animate###########
		function animate(brightAdjust, speedMulti){
			
				
				console.log("animate called");	

				writePixels( simpleSingleBox(boxno, brightness,brightness,brightness));
						
				if (brightness > 1){
					brightness = brightness - brightAdjust;
				} else {
					brightness = 255;
				}
				if (boxno <= 300){
					boxno = boxno + 20;
				} else {
					boxno = 1;
				}
				
				startSpeed = startSpeed + speedMulti;
				boxno++;
				
				
		};
		
		//random color boxes
		function randomColorBoxes(){
			console.log("randoColorBoxes called.");
			
			var rando;
			writePixels(simpleSingleBox(rando = getRandomInt(1, 320),getRandomInt(0,255),getRandomInt(0,255),getRandomInt(0,255)));
		};
		
		//2 color gradient
		function twoColorGradient(){
			console.log("twoColorGradient called.");
			grad.rgb(steps).forEach(function(color, i) {	
			//grad = tinygradient(colors);
			
				
				//console.log(color.toRgbString());
				rgb = frames[i];
				writePixels(simpleSingleBox(i*20,rgb[0],rgb[1],rgb[2]));
				i++;
				});
		
		};
		
		//gradientAnimate###########
		function gradientAnimate(){
			
				
				console.log("gradientAnimate called");
				console.log( "Frameno : " + frameno + ". Length : " + frames.length + " . Boxno : " + boxno);
				if (frameno > frames.length) {
					frameno = 1;
				}
				if (frameno < frames.length){ //if not the last frame
					rgb = frames[frameno];
					writePixels( simpleSingleBox(boxno, rgb[0],rgb[1],rgb[2]));
					
					if (boxno <= 300){ //if not at limit
						boxno = boxno + 20; //increase to next box
					} else {
						boxno = 1; //otherwise reset to 1
					}
				}
				if (frameno != frames.length){ //if not at the end of the grad frames
					rgb = frames[frameno++]; //move to the next one
				} else  {
					frameno = 0; //otherwise start at beginning
				} 
				
	
		};
		
		//gradientAnimatePixel###########
		function gradientAnimatePixel(){
				
				
				console.log("gradientAnimate called");
				console.log( "Frameno : " + frameno + ". Length : " + frames.length + " . Boxno : " + boxno);
				if (frameno > frames.length) { //reset frameno to 1 if outside of length of array
					frameno = 1;
				}
				if (frameno < frames.length){ //if not the last frame
					rgb = frames[frameno]; //set rgb to frame from gradient
					writePixels( singlePixel(pixelno, rgb[0],rgb[1],rgb[2]));
					if (pixelno <= numLEDs){ //if current pixelno is less than numLEDs
						pixelno = pixelno + 1; //increse pixel no by 1
					} else if (pixelno > numLEDs) { //if reach limit of pixels
						pixelno = 1; //reset to 1
					} else {
						pixelno = 1;
					}

				}//end if
				//after writing pixel
				if (frameno != frames.length){//if not at the end of array of gradient steeps
					rgb = frames[frameno++];//move to next gradient step
				} else  {//if at end of grad steps arr

					frameno = 0; //reset to beginning (0)

				} 
				
	
		};
		
		//broadwayChase###########
		function broadwayChase(width){
				console.log("broadwayChase called");
					var rgb = [255,255,255];
					

					var dest = 1; //at some point had to change this from 4 to 1 to keep it working
					   
					
					//var chosen = parseInt(index);
					if (bc <= ledArr.length) {
					//console.log("bc = "+bc+" ledArr.length = "+ledArr.length);
					//console.log("pixel match found : "+chosen)
					dest = (bc*3)+1; //move to correct position
					console.log("dest : "+dest);
						for (i = 0; i < ledArr.length; i++){ //for each led
							//console.log("ledArr[i] : "+ledArr[i]+" should = "+bc);
							if (bc == ledArr[i]){ //if bc selector = current 
								for (j=0; j<width; j++){ //for # of pixels = to width
								console.log("Pulse Start");
								//console.log("R position : "+packet[dest++]);
								packet[dest++] = rgb[0]; //get a turned on LED
								//console.log("G position : "+packet[dest++]);
								packet[dest++] = rgb[1];
								//console.log("B position : "+packet[dest++]);
								packet[dest++] = rgb[2];
								
		
								}//end for	
							}//end if
							else {
					    		packet[dest++] = 0; //darkness
					        	packet[dest++] = 0;
					        	packet[dest++] = 0;
					    	} //end else

						}; //end for each LED
							
					} //endif

					
					//after writing pixel
					if (bc <= (ledArr.length-width)-152){ //if current pixelno is less than numLEDs
						console.log("bc : "+bc+" ledArr lenghth : "+ledArr.length+". width : "+width);
						bc++; //increse pixel no by 1
						console.log(bc);
					} else if (bc > ledArr.length-width) { //if reach limit of pixels
						bc = 1; //reset to 1
					} else {
						bc = 1;
					}
					return packet;
	
		};
		
		
        // Animation loop
        var ganzfield = function() {
            // Get time delta
            var thisTime = (new Date()).getTime();
            var dt = (thisTime - lastTime) * 0.001;
            lastTime = thisTime;
            // Update animation
            phase += frequency * 2 * Math.PI * dt;
            var f = Math.sin(phase);
            writeFrame(
                color.r * (1 + contrast * f),
                color.g * (1 + contrast * f),
                color.b * (1 + contrast * f));
            setTimeout(ganzfield, 1);
        }
		
		//colorVomit###########
		function colorVomit(){
			
				
				console.log("colorVomit called");
				console.log( "Frameno : " + frameno + ". Length : " + frames.length + " . Boxno : " + boxno);
				
				if (frameno > frames.length) {
					frameno = 1;
				}//end if
				if (frameno < frames.length){
					rgb = frames[frameno];
					
					
					writePixels( simpleSingleBox(boxno*20, rgb[0],rgb[1],rgb[2]));
					if (boxno <= numBoxes){
						boxno++;
					} else {
						boxno = 1;
					}
				}
					
				if (frameno != frames.length){ //if not at the end of array of gradient steeps
					rgb = frames[frameno++]; //move to next gradient step
				} else if (frameno = frames.length) { //if at end of grad steps arr
					frameno = 0; //reset to beginning (0)
				}
				

		};

/*function singleBox(ledSelect, r, g, b) {
	var chosen = parseInt(ledSelect);
	var box = new Array(16);
		for (var i = 0; i < 16; i++) {
			box[i] = new Array;
		}//end for
			
	//fill box Array(X16) and sub-arrays(X20) with sequential numbers
	var min = 1;
	for (var j=1; j<17; j++){ //each box starting at 1, end at 16
		var max = j*20; //different max limit for each box
		for (var k=0; k<20; k++) { //each pixel in box 
			box[j-1][k]= min;
			min++;
		}//end pixel for		
		min = max+1;
	}// end box for

	
    for (var i = 0; i < 16; i++) { //each box
		for (var j = 0; j < 20; j++) { //each LED in each box
      		if (box[i][j] == chosen) { //if matches chosen led
      			var firstOfBox = (box[i][0]*3); //3 bytes per led
      			var dest = (firstOfBox + 1);
      			//for each pixel, set r g and b to 255, 0 and 0
       			for (var k = 0; k < 20; k++) { //loop through pixels of selectedBox
       				//console.log(box[i][k]);
        			packet[dest++] = r;
        			packet[dest++] = g;
        			packet[dest++] = b;
        		}//for
     		}//if
    	}//for
 	}//for
 	
 	return packet;
 	
 	//writePixels(blackness);
	//writePixels(blackness);
	
}//end singleBox*/

function multiPixel(list, r, g, b){
	
	//alert(chosen); 
	//console.log(chosen); et below
    var leds = numLEDs;
    
    // Dest position in our packet. Start right after the header.
    var dest = 1; //at some point had to change this from 4 to 1 to keep it working
    
    // Chosen pixel gets RGB values, all others get 0
    for (var led = 0; led <= leds; led++) {
		for (var i = 0; i < list.length ; i++)  {
			var chosen = parseInt(list[i]);
	    	if (led == chosen) {
		    	console.log("pixel match found : "+led)
		    	dest = (led*3)+1; //move to correct position leave 4 0's at beginning of packet as header
	    		packet[dest++] = r;
	        	packet[dest++] = g;
	        	packet[dest++] = b;
	    	} //endif
	    	else {
	    		packet[dest++] = 0;
	        	packet[dest++] = 0;
	        	packet[dest++] = 0;
	    	} //end else
	    }//end for
    } // end for
    	
	console.log("write multi frame");
    return packet;
	

    
}

function singlePixel(index, r, g, b){
	//alert(chosen); 
	//console.log(chosen); et below
    var leds = numLEDs;
    
    // Dest position in our packet. Start right after the header.
    var dest = 1; //at some point had to change this from 4 to 1 to keep it working
    
    // Chosen pixel gets RGB values, all others get 0
    //for (var led = 0; led <= leds; led++) {
			var chosen = parseInt(index);
	    	//if (led == chosen) {
		    	console.log("pixel match found : "+chosen)
		    	dest = (chosen*3)+1; //move to correct position
	    		packet[dest++] = r;
	        	packet[dest++] = g;
	        	packet[dest++] = b;
	    	//} //endif
	    	//else {
	    	//	packet[dest++] = 0;
	        //	packet[dest++] = 0;
	        //	packet[dest++] = 0;
	    	//} //end else
	   
    //} // end for
    return packet;
}

function writePixels(pixels){
	var packet = pixels;
	socket;
	if (socket.readyState != 1 /* OPEN */) {
                // The server connection isn't open. Nothing to do.
                return;
            }

    if (socket.bufferedAmount > packet.length) {
                // The network is lagging, and we still haven't sent the previous frame.
                // Don't flood the network, it will just make us laggy.
                // If fcserver is running on the same computer, it should always be able
                // to keep up with the frames we send, so we shouldn't reach this point.
                return;
            }
    socket.send(packet.buffer);
    console.log("Writing "+(pixels.length-4)/3+" pixels.");
    

	
}//end writePixels