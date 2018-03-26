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
  for(var i=0; i < matches.length; i++) {
    var target = StembureausApp.links_external ? ' target="_blank"' : '';
    $('#results-search').append($(
      '<div class="result">' +
      '<h2><a href="/s/' + matches[i]['gemeente_naam'] + '"' + target + ">" + matches[i]['gemeente_naam'] + '</a></h2>' +
      '</div>'
    ))
  }

  if (matches.length == 0 && query.length > 1) {
    $('#results-search').append($('<p>Helaas, we hebben geen gemeente gevonden voor uw zoekopdracht. Wellicht staat uw gemeente onder een andere naam bekend? Wij gebruiken de officiële spelling van de gemeentenaam, bijvoorbeeld "\'s-Gravenhage" in plaats van "Den Haag".</p>'));
  }
};

StembureausApp.show = function (matches) {
  $('#results-search').empty();
  for(var i=0; i < matches.length; i++) {
    var opinfo = matches[i]['Openingstijden'].split(' tot ');
    var weelchair_labels = {
      'Y': 'Rolstoeltoegankelijk',
      'N': '',
      '': '',
      undefined: ''
    }
    var plaats_naam =  matches[i]['Plaats'] || '<i>Gemeente ' + matches[i]['Gemeente'] + '</i>';
    var adres = '';
    if (typeof(matches[i]['Straatnaam']) !== "object") {
      adres = matches[i]['Straatnaam'] + ' ' + matches[i]['Huisnummer'];
      if (matches[i]['Huisnummertoevoeging']) {
        adres += '-' + matches[i]['Huisnummertoevoeging'];
      }
    }
    var target = StembureausApp.links_external ? ' target="_blank"' : '';
    $('#results-search').append($(
      '<div class="result">' +
      '<h2 class="pull-left"><a href="/s/' + matches[i]['Gemeente'] + '/' + matches[i]['UUID'] + "\"" + target + ">" +  matches[i]['Naam stembureau'] + '</a></h2>' +
      '<p class="pull-right">' + weelchair_labels[matches[i]["Mindervaliden toegankelijk"]] + '</p>' +
      '<h5>' + adres + '</h5>' +
      '<h5><a href="/s/' + matches[i]['Gemeente'] + '"' + target + '>' + plaats_naam + '</a></h5>' +
      '<p>' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '</p>' +
      '</div>'
    ))
  }

  if (matches.length == 0) {
    $('#results-search').append($('<p>Helaas, we hebben niks kunnen vinden. Dit komt waarschijnlijk omdat we alleen zoeken in de lijst van stembureaus, en niet in alle straten. Wilt u weten welk stembureau het dichtst bij u in de buurt is? Gebruik dan de knop \'Gebruik mijn locatie\'.</p>'));
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

  StembureausApp.show(stembureau_matches);
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

$(document).ready(function () {
  StembureausApp.init();

  StembureausApp.stembureaus_markers = [];

  //console.log(StembureausApp.links_external ? 'external links for markers' : 'internal links for markers');

  StembureausApp.getPopup = function(s) {
    var opinfo = StembureausApp.stembureaus[i]['Openingstijden'].split(' tot ');
    var target = StembureausApp.links_external ? ' target="_blank"' : '';
    output = "<p><a href=\"/s/" + StembureausApp.stembureaus[i]['Gemeente'] + '/' + StembureausApp.stembureaus[i]['UUID'] + "\"" + target + ">" + StembureausApp.stembureaus[i]['Naam stembureau'] + "</a><br />";
    if (StembureausApp.stembureaus[i]['Straatnaam']) {
      output += StembureausApp.stembureaus[i]['Straatnaam'];
    }
    if (StembureausApp.stembureaus[i]['Huisnummer']) {
      output += ' ' + StembureausApp.stembureaus[i]['Huisnummer'];
    }
    if (StembureausApp.stembureaus[i]['Huisnummertoevoeging']) {
      output += '-' + StembureausApp.stembureaus[i]['Huisnummertoevoeging'];
    }
    if (StembureausApp.stembureaus[i]['Plaats']) {
      output += "<br />" + StembureausApp.stembureaus[i]['Plaats'] + "<br />";
    } else {
      output += "<i>Gemeente " + StembureausApp.stembureaus[i]['Gemeente'] + "</i><br />";
    }
    output += '<strong>Open:</strong> ' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '<br />';
    if (StembureausApp.stembureaus[i]["Mindervaliden toegankelijk"] == 'Y') {
      output += '<i class="fa fa-wheelchair" aria-hidden="true"></i>';
    }
    output += '</p>';
    return output;
  };

  for(var i=0; i < StembureausApp.stembureaus.length; i++) {
    StembureausApp.stembureaus_markers.push(
      L.marker(
        [StembureausApp.stembureaus[i].Latitude, StembureausApp.stembureaus[i].Longitude]
      ).bindPopup(StembureausApp.getPopup(StembureausApp.stembureaus[i]))
    );
  }

  StembureausApp.map = L.map('map').setView([52.2, 5.592], 6);
  StembureausApp.map._layersMaxZoom = 19;
  StembureausApp.clustermarkers = L.markerClusterGroup({maxClusterRadius: 50});
  for(var i=0; i < StembureausApp.stembureaus_markers.length; i++) {
    StembureausApp.stembureaus_markers[i].addTo(StembureausApp.clustermarkers);
  }

  if (StembureausApp.stembureaus_markers.length > 50) {
    StembureausApp.map.addLayer(StembureausApp.clustermarkers);
  } else {
    StembureausApp.map.addLayer(L.layerGroup(StembureausApp.stembureaus_markers));
  }

  StembureausApp.group = L.featureGroup(StembureausApp.stembureaus_markers.filter(
    function (s) {
      return (StembureausApp.stembureaus_markers.length <= 50) || (s._latlng.lng > 0);
    }));
  StembureausApp.map.fitBounds(StembureausApp.group.getBounds(), {maxZoom: 16});

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="http://osm.org/copyright" target="_blank">OpenStreetMap</a> contributors | <a href="https://waarismijnstemlokaal.nl/" target="_blank">Waar is mijn stemlokaal</a>'
  }).addTo(StembureausApp.map);
});
