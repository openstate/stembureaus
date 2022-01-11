export default {
  init() {
    // JavaScript to be fired on the home page
    console.log('clickmap init!');

    if ($('#clickmap').length) {
      run_clickmap();
    }

  },
  finalize() {
    // JavaScript to be fired on the home page, after the init JS
  },
};

var cmap;

var run_clickmap = function() {
  console.log('gonna init the clickmap now!');
  cmap = L.map('clickmap', {zoomSnap: 0.2}).setView([52.2, 5.3], 7);
  cmap.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank" rel="noopener">Leaflet</a>');

  // Basisregistratie Topografie (BRT) map used when viewing 'Europees Nederland' on our map
  var brt = L.tileLayer(
    'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:3857/{z}/{x}/{y}.png',
    {
      id: 'brt',
      attribution: 'Kaartgegevens &copy; <a href="https://www.kadaster.nl/" target="_blank" rel="noopener">Kadaster</a> | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
  );

  // OpenStreetMap map used when viewing all other places outside 'Europees Nederland' on our map,
  // because BRT doesn't have that data
  var osm = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      id: 'osm',
      attribution: '<a href="http://osm.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
  );

  // Icons
  var icons = {
    'Stembureau': '<i class="fa fa-pencil-alt text-red"></i> ',
    'Stembureau-orange': '<i class="fa fa-pencil-alt text-orange"></i> ',
  };

  // Icons for the map markers
  var markerIcons = {
    'Stembureau': L.AwesomeMarkers.icon(
      {
        prefix: 'fa',
        icon: 'pencil-alt',
        markerColor: 'red'
      }
    ),
    'Stembureau-orange': L.AwesomeMarkers.icon(
      {
        prefix: 'fa',
        icon: 'pencil-alt',
        markerColor: 'orange'
      }
    )
  };

  // Use BRT in 'Europees Nederland' and OSM for the rest
  var zoom = cmap.getZoom();
  var center = cmap.getCenter();
  if (zoom >= 6 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
    cmap.removeLayer(osm);
    cmap.addLayer(brt);
  } else {
    cmap.removeLayer(brt);
    cmap.addLayer(osm);
  }

  // Show BRT only when zoomed in on European Netherlands, use OSM for
  // the rest
  cmap.on('zoom move', function() {
    var zoom = cmap.getZoom();
    var center = cmap.getCenter();
    if (zoom >= 6 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
      cmap.removeLayer(osm);
      cmap.addLayer(brt);
    } else {
      cmap.removeLayer(brt);
      cmap.addLayer(osm);
    }
  });

  var lat = $('#latitude').val();
  var lon = $('#longitude').val();
  var marker;
  if (lat && lon) {
    marker = new L.marker(
      new L.LatLng(lat, lon), {
        draggable:'true',
        icon: markerIcons['Stembureau']
      });
    cmap.addLayer(marker);
  }
};
