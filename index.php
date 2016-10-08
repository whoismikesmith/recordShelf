<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="apple-touch-icon" sizes="57x57" href="media/apple-icon-57x57.png">
	<link rel="apple-touch-icon" sizes="60x60" href="media/apple-icon-60x60.png">
	<link rel="apple-touch-icon" sizes="72x72" href="media/apple-icon-72x72.png">
	<link rel="apple-touch-icon" sizes="76x76" href="media/apple-icon-76x76.png">
	<link rel="apple-touch-icon" sizes="114x114" href="media/apple-icon-114x114.png">
	<link rel="apple-touch-icon" sizes="120x120" href="media/apple-icon-120x120.png">
	<link rel="apple-touch-icon" sizes="144x144" href="media/apple-icon-144x144.png">
	<link rel="apple-touch-icon" sizes="152x152" href="media/apple-icon-152x152.png">
	<link rel="apple-touch-icon" sizes="180x180" href="media/apple-icon-180x180.png">
	<link rel="icon" type="image/png" sizes="192x192"  href="media/android-icon-192x192.png">
	<link rel="icon" type="image/png" sizes="32x32" href="media/favicon-32x32.png">
	<link rel="icon" type="image/png" sizes="96x96" href="media/favicon-96x96.png">
	<link rel="icon" type="image/png" sizes="16x16" href="media/favicon-16x16.png">
	
	<meta name="msapplication-TileColor" content="#ffffff">
	<meta name="msapplication-TileImage" content="media/ms-icon-144x144.png">
	<meta name="theme-color" content="#ffffff">

    <title>recordShelf v3</title>

    <link href="/bootstrap/css/bootstrap.min.css" rel="stylesheet">
    <link href="/bootstrap/css/dashboard.css" rel="stylesheet">
    <!-- <link href="/css/narrow.css" rel="stylesheet"> !-->
    <link rel="stylesheet" type="text/css" href="DataTables/datatables.min.css"/>
    <link rel="stylesheet" href="/jquery-ui.css">

    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
      <script src="https://oss.maxcdn.com/libs/respond.js/1.3.0/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>
	<nav class="navbar navbar-default navbar-fixed-top">
      <div class="container-fluid">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">recordShelf v3</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
          <ul class="nav navbar-nav navbar-right">
            <li class="active"><a href="#" class="fullmode">Full Collection</a></li>
            <li class="dropdown"><a href="#" class="dropdown-toggle supermode" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Superlatives <span class="caret"></span></a>
            	<ul class="dropdown-menu">
	            <li><a href="#" class="labelsbutton">Top Ten Labels</a></li>
	            <li role="separator" class="divider"></li>
	            <li><a href="#" class="artistsbutton">Top Ten Artists</a></li>
          </ul>
            </li>
            <li><a href="#">Settings</a></li>
			  <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Fx <span class="caret"></span></a>
          <ul class="dropdown-menu">
            <li><a href="#">Action</a></li>
            <li><a href="#">Another action</a></li>
            <li><a href="#">Something else here</a></li>
            <li role="separator" class="divider"></li>
            <li><a href="#">Separated link</a></li>
          </ul>
        </li>
          </ul>
          <form class="navbar-form navbar-right">
            <input type="text" class="form-control" placeholder="Search...">
          </form>
        </div>
      </div>
    </nav>
    
    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-3 col-md-2 sidebar">
        	<ul class="nav nav-sidebar">
            <li class="active"><a href="#" class="fullmode">Full Collection<span class="sr-only">(current)</span></a></li>
            <li class="dropdown"><a href="#" class="dropdown-toggle supermode" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Superlatives <span class="caret"></span></a>
            	<ul class="dropdown-menu">
	            <li><a href="#" class="labelsbutton">Top Ten Labels</a></li>
	            <li role="separator" class="divider"></li>
	            <li><a href="#" class="artistsbutton">Top Ten Artists</a></li>
          </ul>
            </li>
            <li><a href="#">Data</a></li>
            <li><a href="#">Something Else</a></li>
          </ul>
        </div>
        
        <div class="col-sm-9 col-sm-offset-3 col-md-10 col-md-offset-2 main">
	      
         <div id="options-container" class="panel panel-default">
	      <div class="panel-body">
		  <div class="row">
		  <div id="colorPick-container" class="col-md-1">
			      <label for="colorpick">Color #1</label>
			      <input class="form-control" id="colorpick" type="color" value="#0000FF" />
		      </div>
		      <div id="colorPick2-container" class="col-md-1">
			  <label for="colorpick2">Color #2</label>
			      <input class="form-control" id="colorpick2" type="color" value="#FFFFFF" />
		      </div>
		      <div id="fxmenu-container" class="col-md-4">
		      <form>
		      <label for="effectsMenu">Pick Effect:</label>
			 	 <select name="effectsMenux" id="effectsMenu" data-role="slider" class="form-control">
					<option id="off" value="1" selected>Off</option>
					<option id="randomcolorboxes" value="2">Random Color Boxes</option>
					<option id="whitestepdown" value="3">White Step Down</option>
					<option id="2colorgradient" value="4">Animated Gradient by Pixel</option>
					<option id="gradientAnimate" value="5">Animated Gradient by Box</option>
					<option id="colorVomit" value="6">Rainbow</option>
					<option id="broadwayChase" value="7">Broadway Chase</option>
					<option id="ganzfield" value="8">ganzfield</option>
				</select>
		      </form>
		      </div><!-- fxmenu cont !-->
		      <div class="col-md-6"></div>
		      </div><!-- row !-->
		      <div id="speedSlider-container">
		      <div class="heading">Speed <input type="text" id="speedVal" readonly style="border:0; font-weight:bold;"></div>
		      <div id="speedSlider"></div></div>
		      <div id="multiSlider-container">
		      <div class="heading">Multiplier <input type="text" id="multiVal" readonly style="border:0; font-weight:bold;"></div>
		      <div id="multiSlider"></div></div>
		      <div id="brightSlider-container">
		      <div class="heading">adjust by x brightness per step <input type="text" id="brightVal" readonly style="border:0; font-weight:bold;"></div>
		      <div id="brightSlider"></div></div>
		       <div id="stepsSlider-container">
		      <div class="heading">gradient steps<input type="text" id="stepsVal" readonly style="border:0; font-weight:bold;"></div>
		      <div id="stepsSlider"></div></div>
		      
	      </div><!-- panel body !-->
      </div> <!-- options !-->
      
      <div id="recordShelf-container" class="panel panel-default">
	      <div class="panel-heading">Full Collection</div>
	      <div class="panel-body">
		  	
			  	<!-- FULL RECORD LIST -->
			  		<table id="main_table" class="table table-striped table-bordered table-hover" width="100%"> <!-- need width 100 or responsive doesn't work!-->
			  			<thead>
			  				<tr>
					            <th>Index</th>
					            <th>Artist</th>
					            <th>Title</th>
					            <th>Label</th>
					            <th>Color</th>
					            <th>Extra</th>
        					</tr>
    					</thead>
						<tbody>
						<?php 
							$config = parse_ini_file('config.ini'); 
							$con=mysql_connect("localhost",$config['username'],$config['password']);
							$db=mysql_select_db($config['dbname'],$con);
							$query=mysql_query("SELECT * FROM twelve_in ORDER by artist");
						
						// Loop through the query results, outputing the options one by one		
							while ($row = mysql_fetch_array($query)) {
					   			echo '<tr class="single_item"><td id="indexVal">'.$row['index'].'</td><td>'.$row['artist'].'</td><td>'.$row['title'].'</td><td>'.$row['label'].'</td><td>'.$row['color'].'</td><td>'.$row['extra'].'</td></tr>';
								}//end while
							
						?>
						</tbody>
					</table>
				</div>
	      
      </div><!-- main_table !-->
      
    <div id="superlatives-container" class="panel panel-default">
	      <div class="panel-heading">Superlatives</div>
	      <div class="panel-body">
			  	<!-- Superlatives -->
			  		<table id="superlatives_table" class="table table-striped table-bordered table-hover"  width="100%">
			  			<thead>
			  				<tr>
					            <th>Name</th>
					            <th>Count</th>
        					</tr>
    					</thead>
					</table>
				
	      </div>
      </div> <!-- superlatives !-->

      <div id="connection-in-progress" class="alert alert-warning hide">
        Connecting...
      </div>

      <div id="connection-error" class="alert alert-danger hide">
        Connection error!
      </div>

      <div id="connection-closed" class="jumbotron hide">
        <h3>Connection closed.</h3>
        <p><button class="btn btn-lg btn-primary connect-button">Reconnect</button></p>
      </div>

      <div id="connection-complete" class="hidden">

        <div class="panel panel-primary">
          <div class="panel-heading">Connected Devices</div>
          <div id="no-devices-connected" class="panel-body">
            <p><strong>No devices are connected!</strong></p>
            <p>If you plug in a Fadecandy board, it will appear here.</p>
          </div>
          <ul id="devices-list" class="list-group"></ul>
        </div> <!-- fadecandy !-->

        <div class="panel panel-info">
          <div class="panel-heading">Server Info</div>
          <div class="panel-body">
            <img src="/media/favicon-96x96.png" class="hidden-xs pull-right" alt="Fc Icon">
            <p>Connected to <code id="server-url"></code></p>
            <p>Server software version <code id="server-version"></code></p>
            <p>Server configuration JSON:</p>
            <pre id="server-config" class="json"></pre>
          </div>
        </div> <!-- info !-->

      </div>

      </div>
      </div><!-- row !-->
      

      <div class="footer">
        <p>&copy; blinkingthings 2016</p>
      </div>

    </div>
    <script src="/dist/js/jquery-2.2.3.js"></script>
    <script src="/bootstrap/js/bootstrap.min.js"></script>
    <script src="/DataTables/datatables.min.js"></script>
    <script src="/js/home.js"></script>
    <script src="/js/recordShelf.js"></script>
    <script src="/jquery-ui.js"></script>
    <script src="/js/tinycolor/tinycolor.js"></script>
    <script src="/js/tinygradient.js"></script>

	<script type="text/javascript">
		
	$(document).ready( function () {
		function top(arr) {// outputs [name, count] of most commonly occuring items in arr[]. 
    var a = [], b = [], prev;
    var c = [], d = [], prev2;
    var minimum = 2;
    
    arr.sort();
    for ( var i = 0; i < arr.length; i++ ) {
        if ( arr[i] !== prev ) {
            a.push(arr[i]);
            b.push(1);
        } else {
            b[b.length-1]++;
        }
        prev = arr[i];
    }
    for (var i = 0; i < b.length; i++) {
    	if (b[i] > minimum){
    		c.push(a[i]);
    		d.push(b[i]);
    	}
    }
    
    //return [a, b];
    return [c, d];
};
		
		//######################## DATATABLE INIT		  	
		var table = $('#main_table').DataTable({
			dom: 'Bfrtip',
			buttons: [
	                'pageLength',
				 {
					text: 'Select Filtered Items',
					action: function ( e, dt, node, config ) {
						table.rows( {order:'index', search:'applied'} ).select();
									}
				},
				
				'selectNone',
				{
                extend: 'collection',
                text: 'Table control',
                buttons: [
                    {
                        text: 'Toggle Color',
                        action: function ( e, dt, node, config ) {
                            dt.column( -2 ).visible( ! dt.column( -2 ).visible() );
                        }
                    },
                    {
                        text: 'Toggle Extra',
                        action: function ( e, dt, node, config ) {
                            dt.column( -1 ).visible( ! dt.column( -1 ).visible() );
                        }
                    }
                ]
            }
            ],
			language: {
				buttons: {
					selectNone: "Select none"
				}
			},
			select: true,
			responsive: true,
			"iDisplayLength": 10
						});
		
		
		var labelData = table.column(':contains(Label)').data().toArray();
		var result = top(labelData);
		for (var i=0; i < result[0].length; i++){
			mostPopularLabels[i] = [result[0][i],result[1][i]];
			//console.log(mostPopularLabels[i]);
			};
		var artistData = table.column(':contains(Artist)').data().toArray();
		var result = top(artistData);
		for (var i=0; i < result[0].length; i++){
			mostPopularArtists[i] = [result[0][i],result[1][i]];
			//console.log(mostPopularArtists[i]);
			};

		
		var table2 = $('#superlatives_table').DataTable({
			responsive: true,
			dom: 'Bfrtip',
    		"aaData": mostPopularArtists,
    		"order": [[ 1, "desc" ]],
			select: true,
			buttons: [
	                'pageLength',
				 {
					text: 'Select Filtered Items',
					action: function ( e, dt, node, config ) {
						table.rows( {order:'index', search:'applied'} ).select();
									}
				},
				
				'selectNone',
				{
                extend: 'collection',
                text: 'Table control',
                buttons: [
                    {
                        text: 'Toggle Color',
                        action: function ( e, dt, node, config ) {
                            dt.column( -2 ).visible( ! dt.column( -2 ).visible() );
                        }
                    },
                    {
                        text: 'Toggle Extra',
                        action: function ( e, dt, node, config ) {
                            dt.column( -1 ).visible( ! dt.column( -1 ).visible() );
                        }
                    }
                ]
            }
			],
			language: {
				buttons: {
					selectNone: "Select none"
				}
			},
			select: true,
			"iDisplayLength": 10
		});
	
		$('.labelsbutton').on( 'click', function () {
			var rows = $("tr.selected");
			table2.rows(rows).deselect();
			table2.destroy();
			//$('#superlatives_table').empty(); // empty in case the columns change
			table2 = $('#superlatives_table').DataTable({
			dom: 'Bfrtip',
    		"aaData": mostPopularLabels,
    		"order": [[ 1, "desc" ]],
			select: true,
			responsive: true,
			buttons: [
	                'pageLength',
				 {
					text: 'Select Filtered Items',
					action: function ( e, dt, node, config ) {
						table.rows( {order:'index', search:'applied'} ).select();
									}
				},
				
				'selectNone',
				{
                extend: 'collection',
                text: 'Table control',
                buttons: [
                    {
                        text: 'Toggle Color',
                        action: function ( e, dt, node, config ) {
                            dt.column( -2 ).visible( ! dt.column( -2 ).visible() );
                        }
                    },
                    {
                        text: 'Toggle Extra',
                        action: function ( e, dt, node, config ) {
                            dt.column( -1 ).visible( ! dt.column( -1 ).visible() );
                        }
                    }
                ]
            }
			],
			language: {
				buttons: {
					selectNone: "Select none"
				}
			},
			select: true,
			responsive: true,
			"iDisplayLength": 10
		});
		} );
		
		$('.artistsbutton').on( 'click', function () {
		var rows = $("tr.selected");
			table2.rows(rows).deselect();
			table2.destroy();
			//$('#superlatives_table').empty(); // empty in case the columns change
			table2 = $('#superlatives_table').DataTable({
			dom: 'Bfrtip',
    		"aaData": mostPopularArtists,
    		"order": [[ 1, "desc" ]],
			select: true,
			responsive: true,
			buttons: [
	                'pageLength',
				 {
					text: 'Select Filtered Items',
					action: function ( e, dt, node, config ) {
						table.rows( {order:'index', search:'applied'} ).select();
									}
				},
				
				'selectNone',
				{
                extend: 'collection',
                text: 'Table control',
                buttons: [
                    {
                        text: 'Toggle Color',
                        action: function ( e, dt, node, config ) {
                            dt.column( -2 ).visible( ! dt.column( -2 ).visible() );
                        }
                    },
                    {
                        text: 'Toggle Extra',
                        action: function ( e, dt, node, config ) {
                            dt.column( -1 ).visible( ! dt.column( -1 ).visible() );
                        }
                    }
                ]
            }
			],
			language: {
				buttons: {
					selectNone: "Select none"
				}
			},
			select: true,
			"iDisplayLength": 10
		});
		} );
		
		$('#superlatives-container').hide(250); //default hide superlatives
		
		$('.fullmode').on( 'click', function () {
			var rows = $("tr.selected");
			table2.rows(rows).deselect(); //deselect all rows from superlatives table
			$(this).parent().addClass('active');
			$('.supermode').parent().removeClass('active');
			$('#recordShelf-container').show();
			$('#superlatives-container').hide();
		} );
		
		$('.supermode').on( 'click', function () {
			var rows = $("tr.selected");
			table.rows(rows).deselect(); //deselect all rows from main table
			$(this).parent().addClass('active');
			$('.fullmode').parent().removeClass('active');
			$('#recordShelf-container').hide();
			$('#superlatives-container').show();
		} );
		
		
		//######################## SLIDERS INIT		  			  		
		$( "#speedSlider" ).slider({
			min: 1,
			max: 500,
			value: 1,
			slide: function( event, ui ) {
				$( "#speedVal" ).val(ui.value );
			}
		});
		
		$( "#multiSlider" ).slider({
			min: 10,
			max: 500,
			value: 500,
			slide: function( event, ui ) {
				$( "#multiVal" ).val(ui.value );
			}

		});
		
		$( "#brightSlider" ).slider({
			min: 10,
			max: 255,
			value: 50,
			slide: function( event, ui ) {
				$( "#brightVal" ).val(ui.value );
			}

		});
		
		$( "#stepsSlider" ).slider({
			min: 2,
			max: 512,
			value: 17,
			slide: function( event, ui ) {
				$( "#stepsVal" ).val(ui.value );
			}

		});
		
		//hide slides + colors
		$("#speedSlider-container").hide(250);
		$("#multiSlider-container").hide(250);
		$("#brightSlider-container").hide(250);
		$("#stepsSlider-container").hide(250);

		//set initial input box values to display sliders values
		$( "#speedVal" ).val($( "#speedSlider" ).slider( "value" ) );
		$( "#multiVal" ).val($( "#multiSlider" ).slider( "value" ) );
		$( "#brightVal" ).val($( "#brightSlider" ).slider( "value" ) );
		$( "#stepsVal" ).val($( "#stepsSlider" ).slider( "value" ) );
		
		
		
		//vars
		
		var sliderSpeed = $( "#speedSlider" ).slider( "value" );
		var speedMulti = $( "#multiSlider" ).slider( "value" );
		var brightAdjust = $( "#brightSlider" ).slider( "value" );
		var steps = $( "#stepsSlider" ).slider( "value" );
		
		var colors = [$("#colorpick").val(),$("#colorpick2").val()]
		//colorpick
		var firstRGB = convertHex($("#colorpick").val());
		activeR = firstRGB[0];
		activeG = firstRGB[1];
		activeB = firstRGB[2];
		//colorpick2
		var firstRGB2 = convertHex($("#colorpick2").val());
		activeR2 = firstRGB2[0];
		activeG2 = firstRGB2[1];
		activeB2 = firstRGB2[2];
		
		
		var grad = tinygradient(colors);//rebuild frames array
			grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
		var revGrad = grad.reverse();
		
		var fxVal = function (){
			return $("#effectsMenu").val();
		};
		
		
		
			//##################################################################
			//###################              SELECT      #####################
			//##################################################################
		table
			.on( 'select', function ( e, dt, type, indexes ) {
				var rowData = table.rows( indexes ).data().toArray(); //rowData full of all info on selected rows
				
				//adds index of selected row to selectedArray if it isn't present already
				for (i = 0; i < rowData.length; i++) { //cycle through selected rows
					var rowData = table.rows( indexes ).indexes();
					var selected = rowData[i] + 1; //selected = index of row +1
					if ($.inArray(selected, selectedArray) == -1) {
						selectedArray.push(selected); //add selector to array if not duplicate
					}//end if
				}//end for
				
				//debug for console.logging every selected index within selectedArray
				console.log('Current Count : ' +selectedArray.length + ' | Current Selection : ');
				for (i = 0; i < selectedArray.length ; i++){
					console.log(selectedArray[i] + ' ');
				}//end for
				
				//converts selectedArray to modifiedArray, adjusting for offset caused by my record
				//collection starting at pixel 81 on the real physical shelf
				for (i = 0; i < selectedArray.length ; i++) {
					var ledSelector = Math.ceil(selectedArray[i]/divFactor);
					console.log('OG LED Selector : ' +ledSelector);
					if (ledSelector > numRecordLEDs) { //sometimes rounding the higher index values results in ledSelector being set to numbers outside the range of numRecordLeds
						ledSelector = numRecordLEDs;
					}
					var modifiedSelect = ledSelector + 80; //modifying for my shelf, not using the first 80 LED's for record catalog
					if ($.inArray(modifiedSelect, modifiedArray) == -1) {
						modifiedArray.push(modifiedSelect);
					}//end if
					
				}//end for
				
				//debug console.logging every selected index within modifiedArray
				console.log('Mod Selector Count : ' + modifiedArray.length + ' | Modified LED Selector(s): ');
				for (i = 0; i < modifiedArray.length ; i++){
					console.log(modifiedArray[i] + ' ');
				}//end for
				console.log('Sending write command...');
				
				//blackout
				writeModArray(0,0,0);
				writeModArray(0,0,0);
				
				//if multiple indexes selected, blink only single pixels. Otherwise blinkBox as well.
				if (modifiedArray.length > 1){
					//multiple selected do this
					blinkMulti(3, 100);
				} else {
					//single selected do this
					blinkBox(3, 100);
					setTimeout(function(){
						blinkSingle(3, 100);
					}, 7*100); //blinkMulti lasts about 700ms so the delay for blinkSingle needs to be at least 700
				}// end if/else			  				
							
				console.log('#######################');
			} )//end on (select)
			
			//##################################################################
			//###################            DESELECT      #####################
			//##################################################################
			.on( 'deselect', function ( e, dt, type, indexes ) {
				var rowData = table.rows( indexes ).data().toArray();
				//moves deslected rows indexes from selectedArray to deletedArray
				for (i = 0; i < rowData.length; i++) { //cycle through selected rows
					var rowData = table.rows( indexes ).indexes();
					var deselected = rowData[i] + 1;
					var index = selectedArray.indexOf(deselected);
					var strSelected = deselected.toString(); //convert deselected index to str
					var selectedLength = strSelected.length; //measure length of deselected
					if (index > -1) {
						console.log("removing "+deselected+" from selection")
						selectedArray.splice(index, selectedLength); //remove deselected from selected array
						console.log("adding "+deselected+" to deletion")

						deletedArray.push(deselected);//add deselected to deletedArray
					}
				}
				
				//debug selectedArray count and contents
				console.log('Current Count : ' +selectedArray.length + ' | Current Selection (deselect) : ');
				for (i = 0; i < selectedArray.length ; i++){
					console.log(selectedArray[i] + ' ');
				}
				//debug deletedArray count and contents
				console.log('Deleted Count : ' +deletedArray.length + ' | Current Deletion : ');
				for (i = 0; i < deletedArray.length ; i++){
					console.log(deletedArray[i] + ' ');
				}
				
				//removes any deselected indexes from modified array
				for (i = 0; i < deletedArray.length ; i++) { //cycle through deletions and compare them to currently selected indexes
					var ledSelector = Math.ceil(deletedArray[i]/divFactor);
					console.log('OG LED Selector : ' +ledSelector);
					if (ledSelector > numRecordLEDs) { //sometimes rounding the higher index values results in ledSelector being set to numbers outside the range of numRecordLeds
						ledSelector = numRecordLEDs;
					}
					var modifiedSelect = ledSelector + 80; //modifying for my shelf, not using the first 80 LED's for record catalog
					console.log('Modded LED Selector : ' +modifiedSelect);
					
					var strSelected = deletedArray[i].toString(); //convert deselected index to str
					var selectedLength = strSelected.length; //measure length of deselected
					modifiedArray.splice( $.inArray(modifiedSelect,modifiedArray), selectedLength);
					
					
					
					
				}//end for
				//debug modifiedArray count and contents	  				
				console.log('Selector Count : ' + modifiedArray.length + ' | Modified LED Selector(s): ');
				for (i = 0; i < modifiedArray.length ; i++){
					console.log(modifiedArray[i] + ' ');
				}//end for
				
				deletedArray = []; //clear deleted 
				console.log('#######################');
								
			} ); //end on (deselect)
			
			//#####################################
			//###   Superlatives Table Select	###
			//#####################################	
			table2.on( 'select', function ( e, dt, type, indexes ) {
				
				var selectedRowData = table2.rows( indexes ).data();
				console.log(selectedRowData);
				
				var rowIdx = table //return object containing indexes of items from the MAIN TABLE who's artist name or label name matches the selectedRow's name field (artist or label)
				    .cells( ':contains("'+selectedRowData[0][0]+'")' ) //sekectedRowData[0] is just the first row if you select more than 1. 
				    .indexes()
				    .pluck( 'row' ) //this is important but I don't quite understand it
				    .sort()
				    .unique();
				
					//console.log(rowIdx.join(', ')); //return object full of indexes
					var indexArray = rowIdx.toArray(); //convert to readable array
					
					$(indexArray).each(function(i){ //for each index in array
						var selected = indexArray[i]+1; //add 1 to make the LED selector accurate
						if ($.inArray(selected, selectedArray) == -1) {
							selectedArray.push(selected); //add selector to array if not duplicate
							}//end if
					});
					
				
				//debug for console.logging every selected index within selectedArray
				console.log('Current Count : ' +selectedArray.length + ' | Current Selection : ');
				for (i = 0; i < selectedArray.length ; i++){
					console.log(selectedArray[i] + ' ');
				}//end for
				
				//converts selectedArray to modifiedArray, adjusting for offset caused by my record
				//collection starting at pixel 81 on the real physical shelf
				for (i = 0; i < selectedArray.length ; i++) {
					var ledSelector = Math.ceil(selectedArray[i]/divFactor);
					console.log('OG LED Selector : ' +ledSelector);
					if (ledSelector > numRecordLEDs) { //sometimes rounding the higher index values results in ledSelector being set to numbers outside the range of numRecordLeds
						ledSelector = numRecordLEDs;
					}
					var modifiedSelect = ledSelector + 80; //modifying for my shelf, not using the first 80 LED's for record catalog
					if ($.inArray(modifiedSelect, modifiedArray) == -1) {
						modifiedArray.push(modifiedSelect);
					}//end if
					
				}//end for
				
				//debug console.logging every selected index within modifiedArray
				console.log('Selector Count : ' + modifiedArray.length + ' | Modified LED Selector(s): ');
				for (i = 0; i < modifiedArray.length ; i++){
					console.log(modifiedArray[i] + ' ');
				}//end for
				console.log('Sending write command...');
				
				//blackout
				writeModArray(0,0,0);
				writeModArray(0,0,0);
				
				//if multiple indexes selected, blink only single pixels. Otherwise blinkBox as well.
				if (modifiedArray.length > 1){
					//multiple selected do this
					blinkMulti(3, 100);
				} else {
					//single selected do this
					blinkBox(3, 100);
					setTimeout(function(){
						blinkSingle(3, 100);
					}, 7*100); //blinkMulti lasts about 700ms so the delay for blinkSingle needs to be at least 700
				}// end if/else			  				
							
				console.log('#######################');  
			} )//end on (select)
			
			//#####################################
			//###  Superlatives Table DE-Select ###
			//#####################################	
			.on( 'deselect', function ( e, dt, type, indexes ) {
	
				var selectedRowData = table2.rows( indexes ).data();
				console.log(selectedRowData);
				
				var rowIdx = table //return object containing indexes of items from the MAIN TABLE who's artist name or label name matches the selectedRow's name field (artist or label)
				    .cells( ':contains("'+selectedRowData[0][0]+'")' ) //sekectedRowData[0] is just the first row if you select more than 1. 
				    .indexes()
				    .pluck( 'row' ) //this is important but I don't quite understand it
				    .sort()
				    .unique();
				
					//console.log(rowIdx.join(', ')); //return object full of indexes
					var indexArray = rowIdx.toArray(); //convert to readable array
					
					$(indexArray).each(function(i){ //for each index in array
						var deselected = indexArray[i]+1; //add 1 to make the LED selector accurate
						var index = selectedArray.indexOf(deselected);
						var strSelected = deselected.toString(); //convert deselected index to str
						var selectedLength = strSelected.length; //measure length of deselected
						if (index > -1) {
							console.log("removing "+deselected+" from selection")
							selectedArray.splice(index, selectedLength); //remove deselected from selected array
							console.log("adding "+deselected+" to deletion")

							deletedArray.push(deselected);//add deselected to deletedArray
						}
					});

				
				//debug selectedArray count and contents
				console.log('Current Count : ' +selectedArray.length + ' | Current Selection (deselect) : ');
				for (i = 0; i < selectedArray.length ; i++){
					console.log(selectedArray[i] + ' ');
				}
				//debug deletedArray count and contents
				console.log('Deleted Count : ' +deletedArray.length + ' | Current Deletion : ');
				for (i = 0; i < deletedArray.length ; i++){
					console.log(deletedArray[i] + ' ');
				}
				
				//removes any deselected indexes from modified array, leaving behind any remaining selected indexes
				for (i = 0; i < deletedArray.length ; i++) { //cycle through deletions and compare them to currently selected indexes
					var ledSelector = Math.ceil(deletedArray[i]/divFactor);
					console.log('OG LED Selector : ' +ledSelector);
					if (ledSelector > numRecordLEDs) { //sometimes rounding the higher index values results in ledSelector being set to numbers outside the range of numRecordLeds
						ledSelector = numRecordLEDs;
					}
					var modifiedSelect = ledSelector + 80; //modifying for my shelf, not using the first 80 LED's for record catalog
					console.log('Modded LED Selector : ' +modifiedSelect);
					
					var strSelected = deletedArray[i].toString(); //convert deselected index to str
					var selectedLength = strSelected.length; //measure length of deselected
					modifiedArray.splice( $.inArray(modifiedSelect,modifiedArray), selectedLength);
					
					
					
					
				}//end for
				//debug modifiedArray count and contents	  				
				console.log('Selector Count : ' + modifiedArray.length + ' | Modified LED Selector(s): ');
				for (i = 0; i < modifiedArray.length ; i++){
					console.log(modifiedArray[i] + ' ');
				}//end for
				
				deletedArray = []; //clear deleted 
				console.log('#######################');
								
			} ); //end on (deselect)
		
		//checks to see if mouse has moved, if it hasnt, clears pixels		
		$(document).on('mousemove', function() {
			if ($("#effectsMenu").val() == 1){
				clearTimeout(mouseMove);
				
				mouseMove = setTimeout(function( indexes ) {
				console.log("Mouse hasn't moved, writing 2 black frames");
				var rows = $("tr.selected");
				table2.rows(rows).deselect(); //deselect all rows from superlatives table
				table.rows(rows).deselect(); //deselect all rows from main table
				writePixels(trueBlack());
				writePixels(trueBlack());
				}, mouseMoveTime);
			};
		});
		
		//input type=color on change change active colors
		$("#colorpick").change(function(){
			var newRGB = convertHex($("#colorpick").val());
			activeR = newRGB[0];
			activeG = newRGB[1];
			activeB = newRGB[2];
			colors[0] = $("#colorpick").val();//upgrade tinygradient colors array
			console.log(convertHex($("#colorpick").val()));
			grad = tinygradient(colors);//rebuild frames array
			i=0;
			grad.rgb(steps).forEach(function(color) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
			if ($("#effectsMenu").val() == 5){
				//do something
				clearInterval(timer4);
				//ar grad = tinygradient(colors);//rebuild frames array
				//	grad.rgb(steps).forEach(function(color, i) {
				//frames[i] = color.toRgbString().match(/\d+/g);
				//i++;
				//});
				timer4 = setInterval(function() { 
					//frameno = 0;
					gradientAnimate();
										}, sliderSpeed)
				}	
		});
		
		//input type=color on change change active colors
		$("#colorpick2").change(function(){
			var newRGB2 = convertHex($("#colorpick2").val());
			activeR2 = newRGB2[0];
			activeG2 = newRGB2[1];
			activeB2 = newRGB2[2];
			colors[1] = $("#colorpick2").val();
			grad = tinygradient(colors);//rebuild frames array
			i=0;
			grad.rgb(steps).forEach(function(color) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
			if ($("#effectsMenu").val() == 5){
				//do something
				clearInterval(timer4);
				//ar grad = tinygradient(colors);//rebuild frames array
				//	grad.rgb(steps).forEach(function(color, i) {
				//frames[i] = color.toRgbString().match(/\d+/g);
				//i++;
				//});
				timer4 = setInterval(function() { 
					//frameno = 0;
					gradientAnimate();
										}, sliderSpeed)
				}	
		});

		

		
		//speedslider change
		$( "#speedSlider" ).on( "slidechange", function() {
			console.log($( "#speedSlider" ).slider( "value" ));
			
			sliderSpeed = $( "#speedSlider" ).slider( "value" );
			clearInterval(timer);
				clearInterval(timer2);
				clearInterval(timer3);
				clearInterval(timer4);
				clearInterval(timer5);
				clearInterval(timer6);
				clearTimeout(mouseMove);
				writeBlackFrame();
				writeBlackFrame();
				
				
				console.log("trigger animate AGAIN"+$("#effectsMenu").val());
				if ($("#effectsMenu").val() == 2){
				//do something
				timer2 = setInterval(function() { 
					randomColorBoxes();
										}, sliderSpeed)
				} else if ($("#effectsMenu").val() == 3){
					//do something
					
					timer = setInterval(function() {
			
					animate(brightAdjust, speedMulti);
				}, sliderSpeed); 
				} else if ($("#effectsMenu").val() == 4){
					//do something
					
					timer3 = setInterval(function() {
			
					gradientAnimatePixel();
				}, sliderSpeed); 
				} else if ($("#effectsMenu").val() == 5){
					//do something
					timer4 = setInterval(function() {
			
					gradientAnimate();
				}, sliderSpeed); 
				} else if ($("#effectsMenu").val() == 6){
					//do something
					timer5 = setInterval(function() {
			
					colorVomit();
				}, sliderSpeed); 
				} else if ($("#effectsMenu").val() == 7){
					//do something
					timer6 = setInterval(function() {
			
					writePixels(broadwayChase(steps));
				}, sliderSpeed); 
				} 
		} );
		//multislider change
		$( "#multiSlider" ).on( "slidechange", function() {
			console.log($( "#multiSlider" ).slider( "value" ));
			speedMulti = $( "#multiSlider" ).slider( "value" );
			
			clearInterval(timer);
				clearInterval(timer2);
				clearInterval(timer4);
				writeBlackFrame();
				writeBlackFrame();
				if ($("#effectsMenu").val() == 2){
				//do something
				timer2 = setInterval(function() { 
					randomColorBoxes();
										}, sliderSpeed)

				
				} else if ($("#effectsMenu").val() == 3){
					//do something
					timer = setInterval(function() {
			
					animate(brightAdjust, speedMulti);
				}, sliderSpeed); 
				} else if ($("#effectsMenu").val() == 5){
					//do something
					timer4 = setInterval(function() {
			
					gradientAnimate();
				}, sliderSpeed); 
				} 
		} );

		//brightSlider change
		$( "#brightSlider" ).on( "slidechange", function() {
			console.log($( "#brightSlider" ).slider( "value" ));
			brightAdjust = $( "#brightSlider" ).slider( "value" );
			
			clearInterval(timer);
				clearInterval(timer2);
				writeBlackFrame();
				writeBlackFrame();
				if ($("#effectsMenu").val() == 2){
				//do something
				timer2 = setInterval(function() { 
					randomColorBoxes();
										}, sliderSpeed)

				
				} else if ($("#effectsMenu").val() == 3){
					//do something
					timer = setInterval(function() {
			
					animate(brightAdjust, speedMulti);
				}, sliderSpeed); 
				} 

				
			
		} );
		
		//stepsSlider change
		$( "#stepsSlider" ).on( "slidechange", function() {
			console.log($( "#stepsSlider" ).slider( "value" ));
			steps = $( "#stepsSlider" ).slider( "value" );
			if ($("#effectsMenu").val() == 5){
				//do something
				clearInterval(timer4);
				writeBlackFrame();
				writeBlackFrame();
				i = 0;
				frames.splice(steps+1,1000);
				grad = tinygradient(colors);//rebuild frames array
				grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
				console.log("Changeing steps : " + steps);
				console.log("Changeing frames.length : " + frames.length);
				timer4 = setInterval(function() { 
					gradientAnimate();
										}, sliderSpeed)

				
				} else if ($("#effectsMenu").val() == 6){
					
				clearInterval(timer5);
				writeBlackFrame();
				writeBlackFrame();
				i = 0;
				frames.splice(steps+1,1000);
				grad = tinygradient(colors);//rebuild frames array
				grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
				console.log("Changeing steps : " + steps);
				console.log("Changeing frames.length : " + frames.length);
					timer5 = setInterval(function() { 
					colorVomit();
										}, sliderSpeed)
				} else if ($("#effectsMenu").val() == 7){
					
				clearInterval(timer6);
				writeBlackFrame();
				writeBlackFrame();
				
				
				console.log("Changeing steps : " + steps);
				
					timer6 = setInterval(function() { 
					writePixels(broadwayChase(steps));
										}, sliderSpeed)
				} else if ($("#effectsMenu").val() == 4){
					
				clearInterval(timer3);
				writeBlackFrame();
				writeBlackFrame();
				i = 0;
				frames.splice(steps+1,1000);
				grad = tinygradient(colors);//rebuild frames array
				grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
				console.log("Changeing steps : " + steps);
				console.log("Changeing frames.length : " + frames.length);
					timer3 = setInterval(function() { 
					gradientAnimatePixel();
										}, sliderSpeed)
				}	
		} );

		//////////////////////////
		// effects menu functions		
		$( "#effectsMenu" ).change(function() {
			onOrOff = $("#effectsMenu option:selected").text();
			console.log($("#effectsMenu option:selected").text());
			console.log(onOrOff);
			
			$("#speedSlider-container").hide(250);
			$("#multiSlider-container").hide(250);
			$("#brightSlider-container").hide(250);
			$("#stepsSlider-container").hide(250);
			
			clearInterval(timer); //kill any running effects
			clearInterval(timer2);
			clearInterval(timer3);
			clearInterval(timer4);
			clearInterval(timer5);
			clearInterval(timer6);
			clearInterval(timer7);
			clearTimeout(mouseMove); //kill mouse timer
			
			//write 2 blank frames to reset to black
			setTimeout(function(){
							writePixels(trueBlack());
							 }, 100);
				setTimeout(function(){
							writePixels(trueBlack());
							 }, 200);
		
			//2nd option - Random Color Boxes
			if ($(this).val() == 2){
				//do something
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").hide(250); 
				startSpeed = 200;
				timer2 = setInterval(function() { 
					randomColorBoxes();
					var sliderSpeed = $( "#speedSlider" ).slider( "value" );
					console.log(sliderSpeed);
				}, sliderSpeed);

			//3rd option - 	White Gradient
			} else if ($(this).val() == 3){
				//do something
				startSpeed = 200;
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").show(250);
				$("#brightSlider-container").show(250);
				$("#stepsSlider-container").hide(250);
				speedMulti = $( "#multiSlider" ).slider( "value" );
				brightAdjust = $( "#brightSlider" ).slider( "value" );
				//alert (brightAdjust); 
				timer = setInterval(function() {
			
				animate(brightAdjust, speedMulti);
				}, sliderSpeed);
			//4th option - Broken Static Gradient
			} else if ($(this).val() == 4){
				//do something
				pixelno = 1; //reset pixelno to 1
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").show(250); 
				timer3 = setInterval(function() { //set loop timer
				colors = [$("#colorpick").val(),$("#colorpick2").val()]; //set colors
				grad = tinygradient(colors);//rebuild frames array
				grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
					gradientAnimatePixel();
				}, sliderSpeed);
			//5th option - Animated Color Gradient
			} else if ($(this).val() == 5){
				//do something
				boxno = 1; //reset boxno to 1
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").show(250);
				timer4 = setInterval(function() {
				colors = [$("#colorpick").val(),$("#colorpick2").val()];
			
				grad = tinygradient(colors);//rebuild frames array
				grad.rgb(steps).forEach(function(color, i) {
				frames[i] = color.toRgbString().match(/\d+/g);
				i++;
				});
					gradientAnimate();
					//twoColorGradient(steps);
				}, sliderSpeed);
			//6th option - 	Animated rainbow Gradient
			} else if ($(this).val() == 6){
				//do something
				boxno = 1; //reset boxno to 1
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").show(250);
				timer5 = setInterval(function() {
					colors = ['red','orange','yellow','green','blue','purple']
					grad = tinygradient(colors);//rebuild frames array
					grad.rgb(steps).forEach(function(color, i) {
					frames[i] = color.toRgbString().match(/\d+/g);
					i++;
					});
					colorVomit();
					
				}, sliderSpeed);
			//7th option - 	broadway
			} else if ($(this).val() == 7){
				//do something
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").show(250);
				timer6 = setInterval(function() {
					
				writePixels(broadwayChase(steps));
					
				}, sliderSpeed);
			//8th option - Ganzfield
			} else if ($(this).val() == 8){
				//do something
				$("#speedSlider-container").show(250);
				$("#multiSlider-container").hide(250);
				$("#brightSlider-container").hide(250);
				$("#stepsSlider-container").show(250);
				timer7 = setInterval(function() {
				color = colors[0];
				frequency = 10;
				contrast = 255;	
				ganzfield();
					
				}, 1);
			//1st option - 	turn everything off
			} else if ($(this).val() == 1) {
				console.log("Cleared timer");	
				clearInterval(timer);//kill everything
				clearInterval(timer2);
				clearInterval(timer3);
				clearInterval(timer4);
				clearInterval(timer5);
				writeBlackFrame();
				writeBlackFrame();

			} //end of drop down box else-ifs
			
		});//doc ready
	  		
	  		
		  		  		
  	//clear any pixels on first load and reload of page
	  setTimeout(function(){
  		writeBlackFrame(), 5000});
		
		setTimeout(function(){
  		writeBlackFrame(), 5200});
		} );
	</script>
  </body>
</html>
