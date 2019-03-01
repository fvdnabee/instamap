var bounds;
var rangeSelector;
var timestamps;

// TODO: do we want to redraw markers already on the map?
var markers_on_map = new Set([]);
var markers = [];
var jsonResponse;

var rssv = eval(document.getElementById('mymapscript').getAttribute('data-rssv'));
var rsev = eval(document.getElementById('mymapscript').getAttribute('data-rsev'));
var max_width_height = 50; // 50 for zoomlevel < 6.5 and 100 for zl >= 6.5

map.on('load', function () {
	setTimestamps();
	setBounds();

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
			setTimestamps();
			updateMap();
        }
    }).dxRangeSelector("instance");
});

function updateMap() {
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

function setTimestamps() {
	var beginDate;
	var endDate;

	if (typeof rangeSelector == "undefined") {
		beginDate = new Date(rssv[0], rssv[1], rssv[2]);
		endDate = new Date(rsev[0], rsev[1], rsev[2]);

	} else {
		beginDate = new Date(rangeSelector.getValue()[0]),
		endDate = new Date(rangeSelector.getValue()[1]);
	}

	var tsBegin = Math.round(beginDate.getTime() / 1000);
	var tsEnd = Math.round(endDate.getTime() / 1000);

	timestamps = [tsBegin, tsEnd];
}

function setBounds() {
	var newBounds = map.getBounds().toArray();
	newBounds = [newBounds[0][0], newBounds[0][1], newBounds[1][0], newBounds[1][1]];

	// round off the elements in newBounds:
	var fixed_length = 6;
	newBounds = newBounds.map(function(each_element){
    		return Number(each_element.toFixed(fixed_length));
	});

	bounds = newBounds;
}

document.getElementById("btn-set-bounds").onclick = function(){
	setBounds();
	updateMap();
};
