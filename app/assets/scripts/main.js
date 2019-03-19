/* ========================================================================
 * DOM-based Routing
 * Based on http://goo.gl/EUTi53 by Paul Irish
 *
 * Only fires on body classes that match. If a body class contains a dash,
 * replace the dash with an underscore when adding it to the object below.
 *
 * .noConflict()
 * The routing is enclosed within an anonymous function so that you can
 * always reference jQuery with $, even when in .noConflict() mode.
 * ======================================================================== */

(function($) {

  // Use this variable to set up the common and page specific functions. If you
  // rename this variable, you will also need to rename the namespace below.
  var Sage = {
    // All pages
    'common': {
      init: function() {
        // JavaScript to be fired on all pages
      },
      finalize: function() {
        // JavaScript to be fired on all pages, after page specific JS is fired
      }
    },
    // Home page
    'home': {
      init: function() {
        // JavaScript to be fired on the home page
      },
      finalize: function() {
        // JavaScript to be fired on the home page, after the init JS
      }
    },
    // About us page, note the change from about-us to about_us.
    'about_us': {
      init: function() {
        // JavaScript to be fired on the about us page
      }
    }
  };

  // The routing fires all common scripts, followed by the page specific scripts.
  // Add additional events for more control over timing e.g. a finalize event
  var UTIL = {
    fire: function(func, funcname, args) {
      var fire;
      var namespace = Sage;
      funcname = (funcname === undefined) ? 'init' : funcname;
      fire = func !== '';
      fire = fire && namespace[func];
      fire = fire && typeof namespace[func][funcname] === 'function';

      if (fire) {
        namespace[func][funcname](args);
      }
    },
    loadEvents: function() {
      // Fire common init JS
      UTIL.fire('common');

      // Fire page-specific init JS, and then finalize JS
      $.each(document.body.className.replace(/-/g, '_').split(/\s+/), function(i, classnm) {
        UTIL.fire(classnm);
        UTIL.fire(classnm, 'finalize');
      });

      // Fire common finalize JS
      UTIL.fire('common', 'finalize');
    }
  };

  // Load Events
  $(document).ready(UTIL.loadEvents);

})(jQuery); // Fully reference jQuery after this point.

var StembureausApp = window.StembureausApp || {stembureaus: [], links_external: false};

StembureausApp.show_gemeenten = function (matches, query) {
  $('#results-search').empty();
  for (var i=0; i < matches.length; i++) {

    // Deal with alternative municipality names
    gemeente_uri = matches[i]['gemeente_naam']
    if (matches[i]['gemeente_naam'] == 'Den Haag') {
      gemeente_uri = "'s-Gravenhage"
    }
    else if (matches[i]['gemeente_naam'] == 'Den Bosch') {
      gemeente_uri = "'s-Hertogenbosch"
    }
    else if (matches[i]['gemeente_naam'] == 'De Friese Meren') {
      gemeente_uri = "De Fryske Marren"
    }
    else if (matches[i]['gemeente_naam'] == 'Noordoost-Friesland') {
      gemeente_uri = "Noardeast-Fryslân"
    }
    else if (matches[i]['gemeente_naam'] == 'Zuidwest-Friesland') {
      gemeente_uri = "Súdwest-Fryslân"
    }

    var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';
    $('#results-search').append($(
      '<div class="result">' +
      '<h2><a href="/s/' + gemeente_uri + '"' + target + ">" + matches[i]['gemeente_naam'] + '</a></h2>' +
      '</div>'
    ))
  }

  if (matches.length == 0 && query.length > 1) {
    $('#results-search').append($('<p>Helaas, we hebben geen gemeente gevonden voor uw zoekopdracht. Wellicht staat uw gemeente onder een andere naam bekend?</p>'));
  }
};

StembureausApp.show = function (matches, query) {
  $('#results-search').empty();
  matches.sort(function (a,b) {return (a['Nummer stembureau'] > b['Nummer stembureau']) ? 1 : ((b['Nummer stembureau'] > a['Nummer stembureau']) ? -1 : 0)});
  for (var i=0; i < matches.length; i++) {
    var opinfo = matches[i]['Openingstijden'].split(' tot ');
    var weelchair_labels = {
      'Y': 'Mindervaliden toegankelijk',
      'N': 'Niet mindervaliden toegankelijk',
      '': '',
      undefined: ''
    }
    var plaats_naam =  matches[i]['Plaats'] || '<i>Gemeente ' + matches[i]['Gemeente'] + '</i>';
    var adres = '';
    if (typeof(matches[i]['Straatnaam']) !== "object") {
      adres = matches[i]['Straatnaam'] + ' ' + matches[i]['Huisnummer'];
      if (matches[i]['Huisletter']) {
        adres += ' ' + matches[i]['Huisletter'];
      }
      if (matches[i]['Huisnummertoevoeging']) {
        adres += ' ' + matches[i]['Huisnummertoevoeging'];
      }
    }
    var nummer_stembureau = '';
    if (matches[i]['Nummer stembureau']) {
      nummer_stembureau = '#' + matches[i]['Nummer stembureau'] + ' '
    }
    var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';
    $('#results-search').append($(
      '<div class="result">' +
      '<h2 class="pull-left"><a href="/s/' + matches[i]['Gemeente'] + '/' + matches[i]['UUID'] + "\"" + target + ">" + nummer_stembureau + matches[i]['Naam stembureau'] + '</a></h2>' +
      '<p class="pull-right">' + weelchair_labels[matches[i]["Mindervaliden toegankelijk"]] + '</p>' +
      '<h5>' + adres + '</h5>' +
      '<h5>' + plaats_naam + '</h5>' +
      '<p>' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '</p>' +
      '</div>'
    ))
  }

  if (matches.length == 0 && query.length > 1) {
    $('#results-search').append($('<p>Helaas, we hebben niks kunnen vinden. Dit komt waarschijnlijk omdat we alleen zoeken in de lijst van stembureaus, en niet in alle straten. Wilt u weten welk stembureau het dichtst bij u in de buurt is? Gebruik dan de knop \'Gebruik mijn locatie\'.</p>'));
  } else if (query.length == 0) {
    StembureausApp.show(StembureausApp.stembureaus);
  }
};

StembureausApp.search_gemeenten = function (query) {
  var gemeenten_matches = StembureausApp.fuse_gemeenten.search(query);
  StembureausApp.show_gemeenten(gemeenten_matches, query);
};

StembureausApp.search = function (query) {
  //console.log('should be searching for : [' + query + '] now ...');
  //console.log(query.split(/\s+/));
  var stembureau_matches = StembureausApp.fuse.search(query);
  //console.log('matches:');
  //console.dir(stembureau_matches);

  StembureausApp.show(stembureau_matches, query);
};

StembureausApp.init = function() {
  var options = {
    shouldSort: true,
    tokenize: true,
    threshold: 0.25,
    location: 0,
    distance: 100,
    maxPatternLength: 32,
    minMatchCharLength: 1,
    keys: [
      "Gemeente",
      "Plaats",
      "Straatnaam",
      "Naam stembureau"
    ]
  };
  StembureausApp.fuse = new Fuse(StembureausApp.stembureaus, options);

  var gemeente_options = {
  shouldSort: true,
  tokenize: true,
  threshold: 0.25,
  location: 0,
  distance: 100,
  maxPatternLength: 32,
  minMatchCharLength: 1,
  keys: [
    "gemeente_naam",
  ]
  };
  StembureausApp.fuse_gemeenten = new Fuse(StembureausApp.alle_gemeenten, gemeente_options);

  $('#form-gemeente-search').submit(function (e) {
    e.preventDefault();
    return false;
  });

  $('#form-gemeente-search input[type="text"]').keyup(function (e) {
    StembureausApp.search_gemeenten($(this).val());
  });

  $('#form-search').submit(function (e) {
    e.preventDefault();
    return false;
  });

  $('#form-search input[type="text"]').keyup(function (e) {
    StembureausApp.search($(this).val());
  });

  $('#btn-location').click(function (e) {
    StembureausApp.map.locate({setView : true, maxZoom: 16});
    return false;
  });
};

// Shows or hides the checklist part of the stembureau edit form
show_or_hide_checklist = function() {
  if($('input[name=show_checklist]:checked').val() == 'Ja') {
    $('.checklist-div').show();
  } else {
    $('.checklist-div').hide();
  }
}

$(document).ready(function () {
  // Stick the header of the overzicht table to the top
  $('.fixed-header').floatThead({
    responsiveContainer: function($table){
      return $table.closest('.table-responsive');
    },
    top: 54
  });

  show_or_hide_checklist();

  $('.edit-form input[name=show_checklist]').on('change', function() {
    show_or_hide_checklist();
  });

  StembureausApp.init();

  StembureausApp.stembureaus_markers = [];

  StembureausApp.getPopup = function(s) {
    var opinfo = StembureausApp.stembureaus[i]['Openingstijden'].split(' tot ');
    var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';
    output = "<p><a href=\"/s/" + StembureausApp.stembureaus[i]['Gemeente'] + '/' + StembureausApp.stembureaus[i]['UUID'] + "\"" + target + ">#" + StembureausApp.stembureaus[i]['Nummer stembureau']  + " " + StembureausApp.stembureaus[i]['Naam stembureau'] + "</a><br />";
    if (StembureausApp.stembureaus[i]['Straatnaam']) {
      output += StembureausApp.stembureaus[i]['Straatnaam'];
    }
    if (StembureausApp.stembureaus[i]['Huisnummer']) {
      output += ' ' + StembureausApp.stembureaus[i]['Huisnummer'];
    }
    if (StembureausApp.stembureaus[i]['Huisletter']) {
      output += ' ' + StembureausApp.stembureaus[i]['Huisletter'];
    }
    if (StembureausApp.stembureaus[i]['Huisnummertoevoeging']) {
      output += ' ' + StembureausApp.stembureaus[i]['Huisnummertoevoeging'];
    }
    if (StembureausApp.stembureaus[i]['Plaats']) {
      output += "<br>" + StembureausApp.stembureaus[i]['Postcode'] + ", " + StembureausApp.stembureaus[i]['Plaats'];
    } else {
      output += "<i>Gemeente " + StembureausApp.stembureaus[i]['Gemeente'] + "</i>";
    }
    if (StembureausApp.stembureaus[i]['Extra adresaanduiding']) {
      output += "<br>" + StembureausApp.stembureaus[i]['Extra adresaanduiding'];
    }
    output += '<br><strong>Open:</strong> ' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '<br>';
    if (StembureausApp.stembureaus[i]["Mindervaliden toegankelijk"] == 'Y') {
      output += '<i class="fa fa-wheelchair" aria-hidden="true" title="Mindervaliden toegankelijk"></i><span class="sr-only">Mindervaliden toegankelijk</span>';
    } else {
      output += '<span class="fa-stack" title="Niet mindervaliden toegankelijk"><i class="fa fa-wheelchair fa-stack-1x" aria-hidden="true"></i><i class="fa fa-ban fa-stack-2x" style="color: Tomato; opacity: 0.75;"></i></span><span class="sr-only">Niet mindervaliden toegankelijk</span>';
    }
    output += '</p>';
    return output;
  };

  for (var i=0; i < StembureausApp.stembureaus.length; i++) {
    StembureausApp.stembureaus_markers.push(
      L.marker(
        [StembureausApp.stembureaus[i]['Latitude'], StembureausApp.stembureaus[i]['Longitude']]
      ).bindPopup(StembureausApp.getPopup(StembureausApp.stembureaus[i]))
    );
  }

 brt = L.tileLayer(
    'https://geodata.nationaalgeoregister.nl/tiles/service/wmts/brtachtergrondkaart/EPSG:3857/{z}/{x}/{y}.png',
    {
      id: 'brt',
      attribution: 'Kaartgegevens &copy; <a href="https://www.kadaster.nl/" target="_blank" rel="noopener">Kadaster</a> | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
 );

 osm = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      id: 'osm',
      attribution: '<a href="http://osm.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
  );

  StembureausApp.map = L.map('map').setView([52.2, 5.592], 6);

  StembureausApp.map.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank" rel="noopener">Leaflet</a>');

  var zoom = StembureausApp.map.getZoom();
  var center = StembureausApp.map.getCenter();
  if (zoom >= 6 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
    StembureausApp.map.removeLayer(osm);
    StembureausApp.map.addLayer(brt);
  } else {
    StembureausApp.map.removeLayer(brt);
    StembureausApp.map.addLayer(osm);
  }

  // Show BRT only when zoomed in on European Netherlands, use OSM for
  // the rest
  StembureausApp.map.on('zoom move', function() {
    var zoom = StembureausApp.map.getZoom();
    var center = StembureausApp.map.getCenter();
    if (zoom >= 6 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
      StembureausApp.map.removeLayer(osm);
      StembureausApp.map.addLayer(brt);
    } else {
      StembureausApp.map.removeLayer(brt);
      StembureausApp.map.addLayer(osm);
    }
  });

  StembureausApp.clustermarkers = L.markerClusterGroup({maxClusterRadius: 50});
  for (var i=0; i < StembureausApp.stembureaus_markers.length; i++) {
    StembureausApp.stembureaus_markers[i].addTo(StembureausApp.clustermarkers);
  }

  StembureausApp.map.addLayer(StembureausApp.clustermarkers);

  StembureausApp.group = L.featureGroup(StembureausApp.stembureaus_markers.filter(
    function (s) {
      return (StembureausApp.stembureaus_markers.length <= 50) || (s._latlng.lng > 0);
    }));

  // Only fit map to bounds if we are not showing the homepage map
  // (i.e. less than e.g. 2000 stembureau)
  if (StembureausApp.stembureaus.length < 2000) {
    StembureausApp.map.fitBounds(StembureausApp.group.getBounds());
  }
});
