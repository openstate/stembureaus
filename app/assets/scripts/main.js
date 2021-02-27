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

// Icons
var icons = {
  'Stembureau': '<i class="fa fa-pencil text-red"></i> ',
  'Afgiftepunt': '<i class="fa fa-envelope text-blue"></i> '
};

// List gemeenten on the homepage
StembureausApp.show_gemeenten = function (matches, query) {
  $('#results-search-gemeenten').empty();
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
    $('#results-search-gemeenten').append($(
      '<div class="result">' +
      '<h2><a href="/s/' + gemeente_uri + '"' + target + ">" + matches[i]['gemeente_naam'] + '</a></h2>' +
      '</div>'
    ))
  }

  if (matches.length == 0 && query.length > 1) {
    $('#results-search-gemeenten').append($('<p>Helaas, we hebben geen gemeente gevonden voor uw zoekopdracht. Wellicht staat uw gemeente onder een andere naam bekend?</p>'));
  }
};

// List locations in rigth panel on the gemeente pages
StembureausApp.show = function (matches, query) {
  $('#results-search').empty();
  matches.sort(function (a,b) {return (a['Nummer stembureau of afgiftepunt'] > b['Nummer stembureau of afgiftepunt']) ? 1 : ((b['Nummer stembureau of afgiftepunt'] > a['Nummer stembureau of afgiftepunt']) ? -1 : 0)});
  for (var i=0; i < matches.length; i++) {
    var opinfo = matches[i]['Openingstijden 17-03-2021'].split(' tot ');
    var weelchair_labels = {
      'Y': 'Mindervaliden toegankelijk',
      'N': 'Niet mindervaliden toegankelijk',
      '': '',
      undefined: ''
    }
    var akoestiek_labels = {
      'Y': 'Akoestiek geschikt voor slechthorenden',
      'N': '',
      '': '',
      undefined: ''
    }
    var mivatoilet_labels = {
      'Y': 'Mindervaliden toilet aanwezig',
      'N': '',
      '': '',
      undefined: ''
    }
    var plaats_naam = matches[i]['Plaats'] || '<i>Gemeente ' + matches[i]['Gemeente'] + '</i>';
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
    if (matches[i]['Nummer stembureau of afgiftepunt']) {
      nummer_stembureau = '#' + matches[i]['Nummer stembureau of afgiftepunt'] + ' '
    }
    var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';
    $('#results-search').append($(
      '<div class="result row">' +
        '<div class="col-xs-12"><hr style="margin: 0; height: 1px; border-color: #888;"></div>' +
        '<div class="col-xs-12 col-sm-7">' +
          '<h2><a href="/s/' + matches[i]['Gemeente'] + '/' + matches[i]['UUID'] + '"' + target + '>' + icons[matches[i]['Stembureau of Afgiftepunt']] + matches[i]['Stembureau of Afgiftepunt'] + ' ' + nummer_stembureau + matches[i]['Naam stembureau of afgiftepunt'] + '</a></h2>' +
          '<h5>' + adres + '</h5>' +
          '<h5>' + plaats_naam + '</h5>' +
        '</div>' +
        '<div class="col-xs-12 col-sm-5" style="padding-top: 24px;">' +
          '<p style="font-size: 12px">' + weelchair_labels[matches[i]["Mindervaliden toegankelijk"]] + '</p>' +
          '<p style="font-size: 12px">' + akoestiek_labels[matches[i]["Akoestiek"]] + '</p>' +
          '<p style="font-size: 12px">' + mivatoilet_labels[matches[i]["Mindervalide toilet aanwezig"]] + '</p>' +
        '</div>' +
      '</div>'
    ))
  }

  if (matches && matches.length == 0 && query && query.length > 0) {
    $('#results-search').append($('<p>Helaas, we hebben niks kunnen vinden. Dit komt waarschijnlijk omdat we alleen zoeken in de lijst van stembureaus, en niet in alle straatnamen. Wilt u weten welk stembureau het dichtst bij u in de buurt is? Gebruik dan de knop \'Gebruik mijn locatie\'.</p>'));
  } else if (typeof query !== 'undefined' && query.length == 0){
    StembureausApp.show(StembureausApp.filtered_locations);
  }
};

StembureausApp.search_gemeenten = function (query) {
  var gemeenten_matches = StembureausApp.fuse_gemeenten.search(query);
  StembureausApp.show_gemeenten(gemeenten_matches, query);
};

// Options for Fuse locations search
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
    "Naam stembureau of afgiftepunt"
  ]
};

StembureausApp.search = function (query) {
  // Create a Fuse fuzzy search for the filtered locations (used on the gemeenten pages)
  StembureausApp.fuse_locations = new Fuse(StembureausApp.filtered_locations, options);
  //console.log('should be searching for : [' + query + '] now ...');
  //console.log(query.split(/\s+/));
  var stembureau_matches = StembureausApp.fuse_locations.search(query);
  //console.log('matches:');
  //console.dir(stembureau_matches);

  StembureausApp.show(stembureau_matches, query);
};

StembureausApp.init = function() {
  // Create an initial Fuse fuzzy search for all locations (used on the gemeenten pages)
  StembureausApp.fuse_locations = new Fuse(StembureausApp.stembureaus, options);

  // Create a Fuse fuzzy search for the gemeenten (used on the homepage)
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

// Creates a list of openingstijden
create_opinfo = function(datums, loc, datum_range) {
  opinfo_output = '<dl class="dl-horizontal">';

  datums.slice(datum_range).forEach(function(datum) {
    var dag = datum.split(' ')[1];
    var opinfo = loc['Openingstijden ' + dag + '-03-2021'].split(' tot ');
    opinfo_output += '<dt style="text-align: left;">' + datum + '</dt>'
    if (opinfo[0].trim()) {
      opinfo_output += '<dd>' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '</dd>';
    } else {
      opinfo_output += '<dd>gesloten</dd>'
    }
  });

  opinfo_output += '</dl>';
  return opinfo_output;
}

// Get the value of currently selected location type for the map filter
get_location_type = function() {
  return $('.location-type-filter.active input').val();
}

// Get the value of currently selected dag for the map filter
get_dag = function() {
  return $('#dag-filter').val();
}

get_query = function() {
  return $('#form-search input[type="text"]').val();
}

$(document).ready(function () {
  // Stick the header of the overzicht table to the top
  $('.fixed-header').floatThead({
    responsiveContainer: function($table){
      return $table.closest('.table-responsive');
    },
    top: 54
  });

  StembureausApp.init();

  // Icons for the map markers
  var markerIcons = {
    'Stembureau': L.AwesomeMarkers.icon(
      {
        prefix: 'fa',
        icon: 'pencil',
        markerColor: 'red'
      }
    ),
    'Afgiftepunt': L.AwesomeMarkers.icon(
      {
        prefix: 'fa',
        icon: 'envelope',
        markerColor: 'blue'
      }
    )
  };

  // Apply filters to the map
  StembureausApp.filter_map = function (location_type, dag) {
    if (StembureausApp.clustermarkers) {
      StembureausApp.map.removeLayer(StembureausApp.clustermarkers);
    }
    StembureausApp.clustermarkers = L.markerClusterGroup({maxClusterRadius: 50});
    StembureausApp.filter_locations(location_type, dag);
    // Save markers to filtered_markers as we use it later to fit bounds
    StembureausApp.filtered_markers = [];
    StembureausApp.filtered_locations.forEach(function (loc) {
      StembureausApp.filtered_markers.push(
        L.marker(
          [
            loc['Latitude'],
            loc['Longitude']
          ],
          {icon: markerIcons[loc['Stembureau of Afgiftepunt']]}
        ).bindPopup(
          StembureausApp.getPopup(loc)
        )
      )
    });
    StembureausApp.filtered_markers.forEach(function (marker) {
      marker.addTo(StembureausApp.clustermarkers);
    });
    StembureausApp.map.addLayer(StembureausApp.clustermarkers);
  }

  location_filter = function(loc) {
    if (location_type == loc['Stembureau of Afgiftepunt']) {
      StembureausApp.filtered_locations.push(loc);
    } else if (location_type == 'alles') {
      StembureausApp.filtered_locations.push(loc);
    }
  }

  // Filter locations
  StembureausApp.filter_locations = function (location_type, dag) {
    StembureausApp.filtered_locations = [];
    StembureausApp.stembureaus.forEach(function (loc) {
      // When you only view a single location, there is no dag filter as
      // all the information is shown on the page
      if (dag) {
        if (dag == 'alles') {
          location_filter(loc);
        } else if (loc['Openingstijden ' + dag + '-03-2021'].split(' tot ')[0].trim()) {
          location_filter(loc);
        }
      } else {
        StembureausApp.filtered_locations.push(loc);
      }
    })
  }

  var datums = [
    'woensdag 10 maart:',
    'donderdag 11 maart:',
    'vrijdag 12 maart:',
    'zaterdag 13 maart:',
    'zondag 14 maart:',
    'maandag 15 maart:',
    'dinsdag 16 maart:',
    'woensdag 17 maart:'
  ]

  // Create the popup which you see when you click on a marker
  StembureausApp.getPopup = function(loc) {
    // First create the openingstijden HTML
    var opinfo_output = '</p><i>Openingstijden</i>';

    // Show openingstijden for all 8 days for afgiftepunten and only the
    // last 3 days for stembureaus
    datum_range = 0;
    if (loc['Stembureau of Afgiftepunt'] == 'Stembureau') {
      datum_range = 5;
    }

    opinfo_output += create_opinfo(datums, loc, datum_range);

    opinfo_output += '<br><br>';

    // Create the final HTML output
    var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';

    output = "<p><b>" + icons[loc['Stembureau of Afgiftepunt']] + loc['Stembureau of Afgiftepunt'] + "</b>";

    output += " <a href=\"/s/" + loc['Gemeente'] + '/' + loc['UUID'] + "\"" + target + ">";
    if (loc['Nummer stembureau of afgiftepunt']) {
      output += "#" + loc['Nummer stembureau of afgiftepunt']  + " ";
    }
    output += loc['Naam stembureau of afgiftepunt'];
    output += "</a><br />";

    if (loc['Straatnaam']) {
      output += loc['Straatnaam'];
    }
    if (loc['Huisnummer']) {
      output += ' ' + loc['Huisnummer'];
    }
    if (loc['Huisletter']) {
      output += ' ' + loc['Huisletter'];
    }
    if (loc['Huisnummertoevoeging']) {
      output += ' ' + loc['Huisnummertoevoeging'];
    }
    if (loc['Plaats']) {
      output += "<br>" + loc['Postcode'] + ", " + loc['Plaats'];
    } else {
      output += "<i>Gemeente " + loc['Gemeente'] + "</i>";
    }
    if (loc['Extra adresaanduiding']) {
      output += "<br>" + loc['Extra adresaanduiding'];
    }

    output += opinfo_output;

    if (loc["Mindervaliden toegankelijk"] == 'Y') {
      output += '<i class="fa fa-wheelchair fa-2x" style="vertical-align: middle;" aria-hidden="true" title="Mindervaliden toegankelijk"></i><span class="sr-only">Mindervaliden toegankelijk</span>&nbsp;';
    } else {
      output += '<span class="fa-stack" title="Niet mindervaliden toegankelijk"><i class="fa fa-wheelchair fa-stack-1x" aria-hidden="true"></i><i class="fa fa-ban fa-stack-2x" style="color: Tomato; opacity: 0.75;"></i></span><span class="sr-only">Niet mindervaliden toegankelijk</span>&nbsp;';
    }
    if (loc["Akoestiek"] == 'Y') {
      output += '<i class="fa fa-deaf fa-2x" style="vertical-align: middle;" aria-hidden="true" title="Akoestiek geschikt voor slechthorenden"></i><span class="sr-only">Akoestiek geschikt voor slechthorenden</span>&nbsp;';
    }
    if (loc["Mindervalide toilet aanwezig"] == 'Y') {
      output += '<i class="fa fa-wheelchair fa-2x" style="vertical-align: middle;" aria-hidden="true" title="Mindervaliden toilet aanwezig"></i><span title="Mindervaliden toilet aanwezig" style="position: relative; top: -8px; left: -10px" aria-hidden="true">WC</span><span class="sr-only">Mindervaliden toilet aanwezig</span>&nbsp;';
    }
    output += '</p>';
    return output;
  };

  StembureausApp.map = L.map('map', {zoomSnap: 0.2}).setView([52.2, 5.3], 7);

  StembureausApp.map.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank" rel="noopener">Leaflet</a>');

 // Basisregistratie Topografie (BRT) map used when viewing 'Europees Nederland' on our map
 brt = L.tileLayer(
    'https://geodata.nationaalgeoregister.nl/tiles/service/wmts/brtachtergrondkaart/EPSG:3857/{z}/{x}/{y}.png',
    {
      id: 'brt',
      attribution: 'Kaartgegevens &copy; <a href="https://www.kadaster.nl/" target="_blank" rel="noopener">Kadaster</a> | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
 );

 // OpenStreetMap map used when viewing all other places outside 'Europees Nederland' on our map,
 // because BRT doesn't have that data
 osm = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      id: 'osm',
      attribution: '<a href="http://osm.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
    }
  );

  // Use BRT in 'Europees Nederland' and OSM for the rest
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

  // Apply updates to the map if the location type filter is clicked
  $('.location-type-filter').click(function() {
    StembureausApp.filter_map(
      location_type=$(this).find('input').val(),
      dag=get_dag()
    );
    StembureausApp.search(get_query());
  });

  // Apply updates to the map if the location type filter is clicked
  $('#dag-filter').change(function() {
    StembureausApp.filter_map(
      location_type=get_location_type(),
      dag=this.value
    );
    StembureausApp.search(get_query());
  });

  // Default view: show all stembureaus and afgiftepunten on the 17th of March
  StembureausApp.filter_map(
    location_type=get_location_type(),
    dag=get_dag()
  );

  // Select the location to fit the bounds of the map to; use all locations if
  // there are less than 50 (useful for debugging), otherwise only show
  // locations with a longitude > 0; this excludes locations in
  // 'Caribisch Nederland' which would make the map zoom out too much
  StembureausApp.group = L.featureGroup(StembureausApp.filtered_markers.filter(
    function (s) {
      return (StembureausApp.filtered_markers.length <= 50) || (s._latlng.lng > 0);
    }
  ));

  // Only fit map to bounds if we are not showing the homepage map
  // (i.e. less than e.g. 2000 stembureau), because we always want to
  // show the whole map of the Netherlands even if we are still
  // collecting the locations; also only fit bounds if there is at least one
  // marker otherwise you get an error
  if (StembureausApp.filtered_markers.length > 0 && StembureausApp.filtered_markers.length < 2000) {
    StembureausApp.map.fitBounds(StembureausApp.group.getBounds(), {padding: [30, 30]});
  }
});
