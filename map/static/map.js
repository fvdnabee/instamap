var bounds;
var rangeSelector;
var timestamps;
var ready = false;

// TODO: do we want to redraw markers already on the map?
var markers_on_map = new Set([]);
var markers = [];
var jsonResponse;

var layer_ids = ["santiago-track", "silkroad-0-track", "silkroad-1-track", "silkroad-2-track", "silkroad-3-track", "silkroad-4-track"]
var tile_ids = ["fvdnabee.5dbhhek7", "fvdnabee.cwn75xfz", "fvdnabee.8uncf7n4", "fvdnabee.1o18xqpn", "fvdnabee.3k6un6tc", "fvdnabee.arcp8dgf"]

var rssv = eval(document.getElementById('mymapscript').getAttribute('data-rssv'));
var rsev = eval(document.getElementById('mymapscript').getAttribute('data-rsev'));
var max_width_height = 50; // 50 for zoomlevel < 6.5 and 100 for zl >= 6.5

map.on('load', function () {
	ready = true;

	addTrackLayers();

	setTimestamps(new Date(rssv[0], rssv[1], rssv[2]), new Date(rsev[0], rsev[1], rsev[2]));
	setBounds(map.getBounds().toArray());

	updateMap();
});

map.on('zoomend', function() {
	if (map.getZoom() < 6.5 && max_width_height != 50) {
		max_width_height = 50;
		draw_map_entries();
	} else if (map.getZoom() >= 6.5 && max_width_height != 100) {
		max_width_height = 100;
		draw_map_entries();
	}
});

//map.on('moveend', function() {
//	updateMap();
//});

function addTrackLayers (){
	for (var i = 0; i < layer_ids.length; i++) {
		map.addLayer({
			"id": layer_ids[i],
			"type": "line",
			"source": {
			type: 'vector',
			url: 'mapbox://' + tile_ids[i]
			},
			"source-layer": "tracks",
			"layout": {
			"line-join": "round",
			"line-cap": "round"
			},
			"paint": {
			"line-color": "#ff0000",
			"line-width": 4
			}
		});
	}

}

$(function(){
	if (typeof DevExpress == "undefined") return;

     rangeSelector = $("#range").dxRangeSelector({
        margin: {
            top: 0
        },
        size: {
            height: 50
        },
        scale: {
			startValue: new Date(rssv[0], rssv[1], rssv[2]),
            endValue: new Date(rsev[0], rsev[1], rsev[2]),
            minorTickInterval: "month",
            tickInterval: "month",
            minorTick: {
                visible: true,
            },
            marker: { visible: false },
            label: {
                format: "MMM yyyy"
            }
        },
        behavior: {
            callValueChanged: "onMovingComplete"
        },
        sliderMarker: {
            format: "dd MMM yyyy"
        },
        //title: "Display posts from the following dates:",
        onValueChanged: function (e) {
			var beginDate = new Date(rangeSelector.getValue()[0]);
			var endDate = new Date(rangeSelector.getValue()[1]);
			setTimestamps(beginDate, endDate);

			updateMap();
        }
    }).dxRangeSelector("instance");
});

function updateMap() {
	if (!ready) return;
	var bounds_uri_query = bounds.join('/');
	var ts_uri_query = timestamps.join('/');

	var oReq = new XMLHttpRequest();
	oReq.open('GET', '/get_map_entries/' + bounds_uri_query + '/' + ts_uri_query);
	oReq.responseType = "json";
	oReq.onload = function() {
	    if (oReq.status === 200) {
			jsonResponse = oReq.response;
			draw_map_entries();
	    }
	    else {
	        alert('Request failed.  Returned status of ' + oReq.status);
	    }
	};
	oReq.send();
}

function draw_map_entries() {
    // Remove all markers:
    markers.forEach(function(m) { m.remove(); });
    markers.length = 0;

    // see: https://docs.mapbox.com/mapbox-gl-js/example/custom-marker-icons/
    jsonResponse.forEach(function(map_entry) {
		var date = new Date(map_entry.ts * 1000);

        // create a DOM element for the marker
        var el = document.createElement('div');

		el.className = 'marker';
		//el.innerHTML = map_entry.loc_name + '; ' + date.toLocaleDateString();
		if (max_width_height > 50) {
			el.innerHTML = map_entry.loc_name.substring(0, 18);
		} else {
			el.innerHTML = '';
		}
        el.style.padding = '1px';
        el.style.backgroundColor = 'white';
        el.style.backgroundImage = 'url(' + map_entry.display_url + ')';
		if (max_width_height > 50) {
			el.style.backgroundPosition = 'center bottom';
		} else {
			el.style.backgroundOrigin = 'content-box';

		}
		el.style.backgroundRepeat = 'no-repeat';

		var w = map_entry.dimensions.width;
		var h = map_entry.dimensions.height;

        var ratioX = max_width_height / w;
        var ratioY = max_width_height / h;
        var ratio = Math.min(ratioX, ratioY);

        var newWidth = Math.floor(w * ratio);
        var newHeight = Math.floor(h * ratio);

		var marker_height = newHeight;
		if (max_width_height > 50) { marker_height += 24; }
        el.style.width = newWidth + 'px';
        el.style.height = marker_height + 'px';
		el.style.backgroundSize = newWidth + 'px ' + newHeight + 'px';

        //el.addEventListener('click', function() {
        //    window.alert(map_entry.caption + '\n\n' + map_entry.url);
        //});

        // add marker to map
        var marker = new mapboxgl.Marker(el)
            .setLngLat([map_entry.lng, map_entry.lat])
            .setPopup(new mapboxgl.Popup({ offset: 25 }) // add popups
		    .setHTML('<p style="margin: 0"><strong><a href="https://www.instagram.com/' + map_entry.username + '">' + map_entry.username + '</a></strong> • <a href="' + map_entry.url + '" title="View post on instagram.com">' + date.toDateString() + '</a></p>' +
			    '<p style="margin: 0; font-family: monospace, monospace;">' + map_entry.loc_name + '</p>' +
			    '<img src="' + map_entry.display_url + '" style="max-width: 400px;" alt="Image not found" />' +
			    '<p style="max-width: 400px; word-wrap: break-word">' + map_entry.caption + '</p>' +
			    '<a href="' + map_entry.url + '" title="View post on instagram.com">' + map_entry.url + '</a>'))
            .addTo(map);

	markers.push(marker);
    });
}

function setTimestamps(beginDate, endDate) {
	var tsBegin = Math.round(beginDate.getTime() / 1000);
	var tsEnd = Math.round(endDate.getTime() / 1000);

	timestamps = [tsBegin, tsEnd];
}

function setBounds(b) {
	var newBounds = [b[0][0], b[0][1], b[1][0], b[1][1]]; // flatten array

	// round off the elements in newBounds:
	var fixed_length = 6;
	newBounds = newBounds.map(function(each_element){
    		return Number(each_element.toFixed(fixed_length));
	});

	bounds = newBounds;
}

document.getElementById("btn-set-bounds").onclick = function(){
	// show all track layers:
    layer_ids.forEach(function(id) { map.setLayoutProperty(id, 'visibility', 'visible'); });

	setBounds(map.getBounds().toArray());
	updateMap();
};

document.getElementById("btn-silkroad").onclick = function(){
	var beginDate = new Date(2018, 01, 01);
	var endDate = new Date(2018, 12, 30);
	if (typeof rangeSelector != "undefined") rangeSelector.setValue([beginDate, endDate]);
	setTimestamps(beginDate, endDate);

	var bounds = [ [-4.507774877735272, 2.6602810808397237], [146.11767796084553, 61.04584048146046] ];
	map.fitBounds(bounds);
	setBounds(bounds);

	// show silkroad track layers, hide santiago layer:
	var layersToHide = [layer_ids[0]];
	var layersToShow = [layer_ids[1], layer_ids[2], layer_ids[3], layer_ids[4], layer_ids[5]];
    layersToHide.forEach(function(id) { map.setLayoutProperty(id, 'visibility', 'none'); });
    layersToShow.forEach(function(id) { map.setLayoutProperty(id, 'visibility', 'visible'); });

	updateMap();
};

document.getElementById("btn-santiago").onclick = function(){
	var beginDate = new Date(2017, 9, 9);
	var endDate = new Date(2017, 12, 31);
	if (typeof rangeSelector != "undefined")  rangeSelector.setValue([beginDate, endDate]);
	setTimestamps(beginDate, endDate);

	var bounds = [ [ -39.27630475468817, 26.781210313359125], [37.25033209346199, 54.85322398321597] ]
	map.fitBounds(bounds);
	setBounds(bounds);

	// show santiago track layer, hide other layers:
	var layersToHide = [layer_ids[1], layer_ids[2], layer_ids[3], layer_ids[4], layer_ids[5]];
	var layersToShow = [layer_ids[0]];
    layersToHide.forEach(function(id) { map.setLayoutProperty(id, 'visibility', 'none'); });
    layersToShow.forEach(function(id) { map.setLayoutProperty(id, 'visibility', 'visible'); });

	updateMap();
};
