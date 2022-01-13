export default {
  init() {
    // JavaScript to be fired on the home page
    console.log('clickmap init!');


  },
  finalize() {
    // JavaScript to be fired on the home page, after the init JS

    if ($('#clickmap').length) {
      run_clickmap();
    }

  },
};

var cmap;
var StembureausApp = window.StembureausApp || {stembureaus: [], links_external: false, muni: null, bag_record: null};

var run_clickmap = function() {
  console.log('gonna init the clickmap now!');
  console.dir('Gemeente:', StembureausApp.gemeente);
  var lat = document.getElementById('latitude').value;
  var lon = document.getElementById('longitude').value;

  var coords = [52.2, 5.3];
  console.log('BAG Record:', StembureausApp.bag_record);
  if (StembureausApp.bag_record) {
    console.log('setting coords to bag record', StembureausApp.bag_record);
    coords = [StembureausApp.bag_record.lat, StembureausApp.bag_record.lon];
  }
  console.log('init coords: ', coords);
  if (lat && lon) {
    coords = [lat, lon];
  } else {
    lat = coords[0];
    lon = coords[1];
  }
  console.log('final coords: ', coords);
  cmap = L.map('clickmap', {zoomSnap: 0.2}).setView(coords, 13);
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

  var marker;
  if (lat && lon) {
    marker = new L.marker(
      new L.LatLng(lat, lon), {
        draggable:'true',
        autoPan: true,
        icon: markerIcons['Stembureau']
      });
    marker.on('dragend', function (e) {
      document.getElementById('latitude').value = marker.getLatLng().lat;
      document.getElementById('longitude').value = marker.getLatLng().lng;
      document.getElementById('x').value = '';
      document.getElementById('y').value = '';

    });
    cmap.addLayer(marker);
    cmap.panTo(new L.LatLng(lat, lon));

    var update_marker = function() {
      var new_lat = document.getElementById('latitude').value;
      var new_lon = document.getElementById('longitude').value;
      var newLatLng = new L.LatLng(new_lat, new_lon);
      console.log('updating marker! ' + new_lat + ',' + new_lon);
      marker.setLatLng(newLatLng);
      cmap.panTo(newLatLng);
    };

    $(document).ready(function () {
      $('#latitude').on('input', function (e) {
          update_marker();
      });
      $('#longitude').on('input', function (e) {
          update_marker();
      });
      // $('#adres_stembureau').on('input', function (e) {
      //   update_marker();
      // });
      $(document).on('stm:address', function (e) {
        console.log('stm:address trigger was fired!');
        update_marker();
      });
    });
  }
};
