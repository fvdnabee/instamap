/*
 * As Instagram blocks public access to www.instagram.com/<user_id>/?__a=1, we
 * use this JS script to crawl a user's feed and store it in a json file. This
 * json file can then be imported into MongoDBvia inscrape_json_mongo.py
 * This script was only tested with Firefox.
 *
 * In order to run this script, you have to be logged in to IG and disable two
 * security settings in order for the script to be able to run in the
 * Webdeveloper Web console:
 * i) Disable CSP: e.g. by setting security.csp.enable to False in about:config
 * ii) Disable CORS: e.g. via the CORS Everywhere extension: https://addons.mozilla.org/en-US/firefox/addon/cors-everywhere/
 *
 * To execute the script, surf to www.instagram.com/<username>/?__a=1. First
 * replace user_id below with the id of the user. Then copy/paste
 * this script into the web developer Web console. At the end a json list of
 * objects should be on your clipboard. If not, reexecute the line copy(...
 * again manually. Save this to a file `user.json' and run the
 * inscrape_json_mongo.py script.
 */

var user_id = xxx;
var query_hash = 'f2405b236d85e8296cf30347c9f08c2a'; // you might have to change this as well, look at the Network in the Web Dev toolbar to get a query hash value
var base_url = 'https://www.instagram.com/graphql/query/?query_hash=' + query_hash + '&variables={"id":"' + user_id + '","first":50';

var edges = [];
var edges_JSON;

var first_request_url= base_url + '}';
scrape_user_page(first_request_url);

function scrape_user_page(user_page) {
	var oReq = new XMLHttpRequest();
	oReq.open('GET', user_page);
	oReq.responseType = "json";
	oReq.withCredentials = true;
	oReq.onload = function() {
	    if (oReq.status === 200) {
			//var json = JSON.parse($('.data').innerText);
			var json = oReq.response;

			edges = edges.concat(json.data.user.edge_owner_to_timeline_media.edges);
			if (json.data.user.edge_owner_to_timeline_media.page_info.has_next_page) {
				new_url = base_url + ',"after":"' + json.data.user.edge_owner_to_timeline_media.page_info.end_cursor + '"}';
				scrape_user_page(new_url);
			} else {
				alert('Fetched all edges. See edges variable');
				edges_JSON = JSON.stringify(edges);
				copy(JSON.stringify(edges, null, 2))
				//window.open('application/json; charset=utf-8,' + escape(edges_JSON));
			}
	    }
	    else {
	        alert('Request failed.  Returned status of ' + oReq.status);
	    }
	};
	oReq.send();
}
