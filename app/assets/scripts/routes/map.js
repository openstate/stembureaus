import Fuse from 'fuse.js';

var weelchair_labels = {
  'ja': '<span class="fa-stack" title="Toegankelijk voor mensen met een lichamelijke beperking"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-check fa-stack-1x"></i></span><span class="sr-only">Toegankelijk voor mensen met een lichamelijke beperking</span>&nbsp;',
  'nee': '<span class="fa-stack" title="Niet toegankelijk voor mensen met een lichamelijke beperking"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-xmark fa-stack-1x"></i></span><span class="sr-only">Niet toegankelijk voor mensen met een lichamelijke beperking</span>&nbsp;'
}

var akoestiek_labels = {
  'ja': '<span class="fa-stack" title="Akoestiek geschikt voor slechthorenden"><i class="fa fa-volume-mute fa-stack-2x" aria-hidden="true"></i><i class="fa fa-check fa-stack-1x"></i></span><span class="sr-only">Akoestiek niet geschikt voor slechthorenden</span>&nbsp;',
  'nee': '<span class="fa-stack" title="Akoestiek niet geschikt voor slechthorenden"><i class="fa fa-volume-mute fa-stack-2x" aria-hidden="true"></i><i class="fa fa-xmark fa-stack-1x"></i></span><span class="sr-only">Akoestiek niet geschikt voor slechthorenden</span>&nbsp;',
  '': '<span class="fa-stack" title="Onbekend of akoestiek geschikt is voor slechthorenden"><i class="fa fa-volume-mute fa-stack-2x" aria-hidden="true"></i><i class="fa fa-question fa-stack-1x"></i></span><span class="sr-only">Onbekend of akoestiek niet geschikt is voor slechthorenden</span>&nbsp;',
  'undefined': '<span class="fa-stack" title="Onbekend of akoestiek niet geschikt is voor slechthorenden"><i class="fa fa-volume-mute fa-stack-2x" aria-hidden="true"></i><i class="fa fa-question fa-stack-1x"></i></span><span class="sr-only">Onbekend of akoestiek niet geschikt is voor slechthorenden</span>&nbsp;'
}

var gehandicaptentoilet_labels = {
  'ja': '<span class="fa-stack" title="Gehandicaptentoilet aanwezig"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-check fa-stack-1x stack"></i></span><span class="wc" title="Gehandicaptentoilet aanwezig" aria-hidden="true">WC</span><span class="sr-only">Gehandicaptentoilet aanwezig</span>&nbsp;',
  'nee': '<span class="fa-stack" title="Geen gehandicaptentoilet"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-xmark fa-stack-1x stack"></i></span><span class="wc" title="Geen gehandicaptentoilet" aria-hidden="true">WC</span><span class="sr-only">Geen gehandicaptentoilet</span>&nbsp;',
  '': '<span class="fa-stack" title="Onbekend of er een gehandicaptentoilet is"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-question fa-stack-1x stack"></i></span><span class="wc" title="Onbekend of er een gehandicaptentoilet is" aria-hidden="true">WC</span><span class="sr-only">Onbekend of er een gehandicaptentoilet is</span>&nbsp;',
  'undefined': '<span class="fa-stack" title="Onbekend of er een gehandicaptentoilet is"><i class="fa fa-wheelchair fa-stack-2x" aria-hidden="true"></i><i class="fa fa-question fa-stack-1x stack"></i></span><span class="wc" title="Onbekend of er een gehandicaptentoilet is" aria-hidden="true">WC</span><span class="sr-only">Onbekend of er een gehandicaptentoilet is</span>&nbsp;'
}

export default {
  // JavaScript to be fired on pages that contain the map
  init() {
    var StembureausApp = window.StembureausApp || {stembureaus: [], links_external: false};

    // Icons
    var icons = {
      'Stembureau': '<i class="fa fa-pencil-alt text-red"></i> ',
      'Stembureau-orange': '<i class="fa fa-pencil-alt text-orange"></i> ',
    };

    // List gemeenten on the homepage
    StembureausApp.show_gemeenten = function (matches, query) {
      $('#results-search-gemeenten').empty();
      for (var i=0; i < matches.length; i++) {

        // Deal with alternative municipality names
        var gemeente_uri = matches[i]['item']['gemeente_naam']
        if (matches[i]['item']['gemeente_naam'] == 'Den Haag') {
          gemeente_uri = "'s-Gravenhage"
        }
        else if (matches[i]['item']['gemeente_naam'] == 'Den Bosch') {
          gemeente_uri = "'s-Hertogenbosch"
        }
        else if (matches[i]['item']['gemeente_naam'] == 'De Friese Meren') {
          gemeente_uri = "De Fryske Marren"
        }
        else if (matches[i]['item']['gemeente_naam'] == 'Noordoost-Friesland') {
          gemeente_uri = "Noardeast-Fryslân"
        }
        else if (matches[i]['item']['gemeente_naam'] == 'Zuidwest-Friesland') {
          gemeente_uri = "Súdwest-Fryslân"
        }

        var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';
        $('#results-search-gemeenten').append($(
          '<ul>' +
          '<li><h3><a href="/s/' + gemeente_uri + '"' + target + ">" + matches[i]['item']['gemeente_naam'] + '</a><h3></li>' +
          '</ul>'
        ))
      }

      if (matches.length == 0 && query.length > 1) {
        $('#results-search-gemeenten').append($('<p>Helaas, we hebben geen gemeente gevonden voor uw zoekopdracht. Wellicht staat uw gemeente onder een andere naam bekend?</p>'));
      }
    };

    // List locations in rigth panel on the gemeente pages
    StembureausApp.show = function (matches, query) {
      $('#results-search').empty();

      matches.sort(function (a,b) {return (a['Nummer stembureau'] > b['Nummer stembureau']) ? 1 : ((b['Nummer stembureau'] > a['Nummer stembureau']) ? -1 : 0)});

      for (var i=0; i < matches.length; i++) {

        var extra_adresaanduiding = '';
        var orange_icon = '';
        if (matches[i]['Extra adresaanduiding'].trim()) {
          // CODE BELOW WAS ONLY NEEDED IN 2021/2022 DUE TO COVID, UNCOMMENT IF IT IS NEEDED AGAIN
          //if (matches[i]['Extra adresaanduiding'].toLowerCase().includes('niet open voor algemeen publiek')) {
          //  extra_adresaanduiding = '<p style="color: #D63E2A"><b>NB: ' + matches[i]['Extra adresaanduiding'] + ' <span style="color: dimgrey"><i class="fa fa-question-circle" data-toggle="popover" data-placement="auto" data-html="true" data-trigger="click" title="<b>Stembureau met beperkte toegang</b>" data-content="Vanwege de risico\'s van de Covid-19 pandemie heeft dit stembureau beperkte toegang. Dat kan bijvoorbeeld handig zijn voor stemlokalen op plaatsen waar extra bescherming gewenst is, bijvoorbeeld in verzorgingshuizen. Hier kan dan alleen worden gestemd door de kiezers die rechtmatig op die locatie mogen verblijven. Omdat het voor andere kiezers dan niet mogelijk is om op de gang van zaken toe te zien, is er in deze stembureaus een onafhankelijke waarnemer aanwezig. Zie Tijdelijke wet verkiezingen COVID-19 art. 4."></i></span></b></p>';
          //  orange_icon = '-orange';
          //} else {
            extra_adresaanduiding = '<p>' + matches[i]['Extra adresaanduiding'] + '</p>';
          //}
        }

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

        var verkiezingen = '';
        if (matches[i].Verkiezingen?.trim()) {
            verkiezingen = '<b>Waterschapsverkiezingen voor</b>: <br>';
            verkiezingen += '<ul style="list-style-type: disc;">';
            matches[i]['Verkiezingen'].trim().split(';').forEach(el => verkiezingen += '<li>' + el.replace('waterschapsverkiezingen voor ', '') + '</li>');
            verkiezingen += '</ul><br>';
        }

        var plaats_naam = matches[i]['Plaats'] || '<i>Gemeente ' + matches[i]['Gemeente'] + '</i>';

        var nummer_stembureau = '';
        if (matches[i]['Nummer stembureau']) {
          nummer_stembureau = '#' + matches[i]['Nummer stembureau'] + ' '
        }

        var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';

        $('#results-search').append($(
          '<ul style="padding: 0">' +
            '<li>' +
              '<div class="col-xs-12" style="margin-bottom: 15px;">' +
                '<h3><a href="/s/' + matches[i]['Gemeente'] + '/' + matches[i]['UUID'] + '"' + target + '>' + icons['Stembureau' + orange_icon] + ' ' + nummer_stembureau + matches[i]['Naam stembureau'] + '</a></h3>' +

                '<div style="padding-left: 26px; color: dimgrey;">' +
                  '<p>' +
                    adres + '<br>' +
                    plaats_naam +
                  '</p>' +
                  extra_adresaanduiding +

                  verkiezingen +

                  '<span class="stembureau-info-icons">' +
                    weelchair_labels[matches[i]["Toegankelijk voor mensen met een lichamelijke beperking"]] +
                    akoestiek_labels[matches[i]["Akoestiek geschikt voor slechthorenden"]] +
                    gehandicaptentoilet_labels[matches[i]["Gehandicaptentoilet"]] +
                  '</span>' +
                  '<br>' +
                  '<b>Visuele hulpmiddelen</b> <i class="fa fa-question-circle" data-toggle="popover" data-placement="auto" data-html="true" data-trigger="click" data-content="Er is verplicht een leesloep aanwezig in elk stembureau"></i>: ' +
                  matches[i]["Visuele hulpmiddelen"] +
                  '<br>' +
                  '<b>Auditieve hulpmiddelen</b>: ' + matches[i]["Auditieve hulpmiddelen"] +
                '</div>' +
              '</div>' +
              '<div class="col-xs-12"><hr style="margin: 0; height: 1px;"></div>' +
            '</li>' +
          '</ul>'
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
        "Naam stembureau"
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

      // Flatten the matches array a bit by removing the 'item' level;
      // this is needed to match our 'filtered_locations' array which we
      // also pass to the 'StembureausApp.show' function
      var cleaned_stembureau_matches = [];
      stembureau_matches.forEach(function(match) {
        cleaned_stembureau_matches.push(match['item']);
      });

      StembureausApp.show(cleaned_stembureau_matches, query);
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
    var create_opinfo = function(loc) {
      var openingstijd = new Date(loc['Openingstijd']);
      var opinfo_output = '<dl class="dl-horizontal">';

      opinfo_output += `<dt style="text-align: left;">${openingstijd.toLocaleDateString('nl-NL', {weekday: 'long', month: 'long', day: 'numeric'})}: </dt>`
      opinfo_output += `<dd style="color: green">${loc['Openingstijd'].split('T')[1].slice(0, 5)} &dash; ${loc['Sluitingstijd'].split('T')[1].slice(0, 5)}</dd>`;

      opinfo_output += '</dl>';
      return opinfo_output;
    }

    var get_query = function() {
      return $('#form-search input[type="text"]').val();
    }

    var run_stembureaus = function () {
      StembureausApp.init();

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

      //var dag;

      // Apply filters to the map
      StembureausApp.filter_map = function (filters) {
        if (StembureausApp.clustermarkers) {
          StembureausApp.map.removeLayer(StembureausApp.clustermarkers);
        }
        StembureausApp.clustermarkers = L.markerClusterGroup({maxClusterRadius: 50});
        StembureausApp.filter_locations(filters);
        // Save markers to filtered_markers as we use it later to fit bounds
        StembureausApp.filtered_markers = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var icon = markerIcons['Stembureau'];
          var orange_icon = '';
          // CODE BELOW WAS ONLY NEEDED IN 2021/2022 DUE TO COVID, UNCOMMENT IF IT IS NEEDED AGAIN
          //if (loc['Extra adresaanduiding'].toLowerCase().includes('niet open voor algemeen publiek')) {
          //  var orange_icon = '-orange';
          //}
          StembureausApp.filtered_markers.push(
            L.marker(
              [
                loc['Latitude'],
                loc['Longitude']
              ],
              {icon: markerIcons['Stembureau' + orange_icon]}
            ).bindPopup(
              StembureausApp.getPopup(loc, orange_icon), {maxWidth: 240, autoPanPaddingTopLeft: L.point(5,75)}
            )
          );
        });
        StembureausApp.filtered_markers.forEach(function (marker) {
          marker.addTo(StembureausApp.clustermarkers);
        });
        StembureausApp.map.addLayer(StembureausApp.clustermarkers);

      };

      // Filter locations
      StembureausApp.filter_locations = function (filters) {
        StembureausApp.filtered_locations = [];

        // Might be used again if elections last multiple days
        //// Filter: dag
        StembureausApp.stembureaus.forEach(function (loc) {
        //  var dag = filters['dag'];
        //  if (dag) {
        //    if (dag === '') {
        //      StembureausApp.filtered_locations.push(loc);
        //    } else if (loc['Openingstijden ' + dag + '-03-2022'].split(' tot ')[0].trim()) {
        //      StembureausApp.filtered_locations.push(loc);
        //    }
        //  } else {
            // When you only view a single location, there is no dag filter as
            // all the information is shown on the page
            StembureausApp.filtered_locations.push(loc);
        //  }
        });

        // Filter: openingstijden
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var openingstijden = filters['openingstijden'];
          if (openingstijden) {
            if (openingstijden === '') {
              temp_filtered_locations.push(loc);
            } else if (openingstijden === 'regulier') {
              if (loc['Openingstijd'] === '2023-11-22T07:30:00' && loc['Sluitingstijd'] === '2023-11-22T21:00:00') {
                temp_filtered_locations.push(loc);
              }
            } else if (openingstijden === 'afwijkend') {
              if (loc['Openingstijd'] !== '2023-11-22T07:30:00' || loc['Sluitingstijd'] !== '2023-11-22T21:00:00') {
                temp_filtered_locations.push(loc);
              }
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;

        // Filter: toegankelijk voor mensen met een lichamelijke beperking
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var toegankelijk = filters['toegankelijk'];
          if (toegankelijk) {
            if (toegankelijk === '') {
              temp_filtered_locations.push(loc);
            } else if (loc['Toegankelijk voor mensen met een lichamelijke beperking'] === toegankelijk) {
              temp_filtered_locations.push(loc);
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;

        // Filter: visuele hulpmiddelen
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var this_filter = filters['visuele-hulpmiddelen'];
          if (this_filter) {
            if (this_filter === '') {
              temp_filtered_locations.push(loc);
            } else if (loc['Visuele hulpmiddelen']) {
              temp_filtered_locations.push(loc);
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;

        // Filter: auditieve hulpmiddelen
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var this_filter = filters['auditieve-hulpmiddelen'];
          if (this_filter) {
            if (this_filter === '') {
              temp_filtered_locations.push(loc);
            } else if (loc['Auditieve hulpmiddelen']) {
              temp_filtered_locations.push(loc);
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;

        // Filter: gehandicaptentoilet
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var this_filter = filters['gehandicaptentoilet'];
          if (this_filter) {
            if (this_filter === '') {
              temp_filtered_locations.push(loc);
            } else if (loc['Gehandicaptentoilet'] === this_filter) {
              temp_filtered_locations.push(loc);
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;

        // Filter: akoestiek
        var temp_filtered_locations = [];
        StembureausApp.filtered_locations.forEach(function (loc) {
          var this_filter = filters['akoestiek'];
          if (this_filter) {
            if (this_filter === '') {
              temp_filtered_locations.push(loc);
            } else if (loc['Akoestiek geschikt voor slechthorenden'] === this_filter) {
              temp_filtered_locations.push(loc);
            }
          } else {
            temp_filtered_locations.push(loc);
          }
        });
        StembureausApp.filtered_locations = temp_filtered_locations;
      };

      // Create the popup which you see when you click on a marker
      StembureausApp.getPopup = function(loc, orange_icon) {
        // First create the openingstijden HTML
        var opinfo_output = '</p><i>Openingstijden</i>';
        opinfo_output += create_opinfo(loc);
        opinfo_output += '<br><br>';

        // Create the final HTML output
        var target = StembureausApp.links_external ? ' target="_blank" rel="noopener"' : '';

        var output = '';

        // Show which gemeente this stembureau belongs to only on the homepage map
        if (StembureausApp.homepage) {
          output += '<i class="fa fa-users text-dark-blue"></i> <a href=\"/s/' + loc['Gemeente'] + '\"' + target + ">Gemeente " + loc['Gemeente'] + "</a><br><br>";
        }

        output += "<b>" + icons['Stembureau' + orange_icon] + "</b>";

        output += " <b><a href=\"/s/" + loc['Gemeente'] + '/' + loc['UUID'] + "\"" + target + ">";
        if (loc['Nummer stembureau']) {
          output += "#" + loc['Nummer stembureau']  + " ";
        }
        output += loc['Naam stembureau'];
        output += "</a></b><br>";

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
          // CODE BELOW WAS ONLY NEEDED IN 2021/2022 DUE TO COVID, UNCOMMENT IF IT IS NEEDED AGAIN
          //if (loc['Extra adresaanduiding'].toLowerCase().includes('niet open voor algemeen publiek')) {
          //  output += '<br><span style="color: #D63E2A"><b>NB: ' + loc['Extra adresaanduiding'] + '</b></span>';
          //} else {
            output += '<br>' + loc['Extra adresaanduiding'];
          //}
        }

        output += '<br><a href="https://geohack.toolforge.org/geohack.php?language=en&params=' + loc['Latitude'] + '_N_' + loc['Longitude'] + '_E_type:landmark&pagename=Stembureau ' + loc['Naam stembureau'] + '" target="_blank" rel="noopener">route (via externe dienst)</a>';

        // ONLY RELEVANT FOR GEMEENTERAADSVERKIEZINGEN
        //if (loc['Gemeente'] == 'Amsterdam') {
        //  output += '<br><br><button class="btn btn-default btn-xs" type="button" data-toggle="collapse" data-target="#collapseFilter-' + loc['UUID'] + '" aria-expanded="false" aria-controls="collapseFilter-' + loc['UUID'] + '">Info over commissieverkiezingen</button><div class="collapse" id="collapseFilter-' + loc['UUID'] + '">NB: tijdens de gemeenteraadsverkiezingen zijn er in Amsterdam ook commissieverkiezingen, daarvoor moet u stemmen in een stembureau in het stadsdeel of stadsgebied dat op uw stempas staat.<br></div>'
        //}

        //if (loc['Gemeente'] == 'Rotterdam') {
        //  output += '<br><br><button class="btn btn-default btn-xs" type="button" data-toggle="collapse" data-target="#collapseFilter-' + loc['UUID'] + '" aria-expanded="false" aria-controls="collapseFilter-' + loc['UUID'] + '">Info over wijkraadverkiezingen</button><div class="collapse" id="collapseFilter-' + loc['UUID'] + '">NB: tijdens de gemeenteraadsverkiezingen zijn er in Rotterdam ook wijkraadverkiezingen, daarvoor moet u stemmen in een stembureau in de wijkraad die op uw stempas staat.<br></div>'
        //}

        if (loc.Verkiezingen?.trim()) {
            output += '<br><br><b>Waterschapsverkiezingen voor</b>:';
            output += '<ul style="list-style-type: disc; margin: 0;">';
            loc['Verkiezingen'].trim().split(';').forEach(el => output += '<li>' + el.replace('waterschapsverkiezingen voor ', '') + '</li>');
            output += '</ul>';
        }

        output += opinfo_output;

        output += '<span class="stembureau-info-icons">';

        output += weelchair_labels[loc["Toegankelijk voor mensen met een lichamelijke beperking"]];
        output += akoestiek_labels[loc["Akoestiek geschikt voor slechthorenden"]];
        output += gehandicaptentoilet_labels[loc["Gehandicaptentoilet"]];

        output += '</br>';
        output += '<b>Visuele hulpmiddelen</b> (NB: er is verplicht een leesloep aanwezig in elk stembureau): ' + loc["Visuele hulpmiddelen"] ;
        output += '</br>';
        output += '<b>Auditieve hulpmiddelen</b>: ' + loc["Auditieve hulpmiddelen"];

        output += '</span>';

        return output;
      };

      var opts = {
        style: 'standaard',
        target: 'map',
        center: {
          latitude: 52.2,
          longitude: 5.3
        },
        overlay: 'false',
        marker: false,
        search: true
      };
      StembureausApp.map = nlmaps.createMap(opts);

      if (StembureausApp.homepage) {
        StembureausApp.map.setZoom(7);
      }

      StembureausApp.map.options.zoomSnap = 0.2;

      // Clear the default attributions set by nlmaps
      StembureausApp.map.attributionControl._attributions = {};

      // Basisregistratie Topografie (BRT) map used when viewing 'Europees Nederland' on our map
      var brt = L.tileLayer(
        'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:3857/{z}/{x}/{y}.png',
        {
          id: 'brt',
          attribution: 'Kaartgegevens &copy; <a href="https://www.kadaster.nl/" target="_blank" rel="noopener">Kadaster</a> | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
        }
      );

      // Alternative for BRT, luchtfoto
      var hwh = L.tileLayer(
        'https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/Actueel_ortho25/EPSG:3857/{z}/{x}/{y}.png',
        {
          id: 'hwh',
          attribution: 'Kaartgegevens &copy; <a href="https://www.kadaster.nl/" target="_blank" rel="noopener">Kadaster</a> | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
        }
      );

      var baseLayers = {
        "Kaart": brt,
        "Luchtfoto": hwh
      };

      // OpenStreetMap map used when viewing all other places outside 'Europees Nederland' on our map,
      // because BRT doesn't have that data
      var osm = L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          id: 'osm',
          attribution: '<a href="http://osm.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors | <a href="https://waarismijnstemlokaal.nl/" target="_blank" rel="noopener">Waar is mijn stemlokaal</a>'
        }
      );

      var chooseLayers = L.control.layers(baseLayers, {}, {position: 'bottomright', collapsed: false})

      // Use BRT in 'Europees Nederland' and OSM for the rest
      var zoom = StembureausApp.map.getZoom();
      var center = StembureausApp.map.getCenter();
      if (zoom >= 7 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
        StembureausApp.map.addLayer(brt);
        chooseLayers.addTo(StembureausApp.map);
        StembureausApp.map.setMaxZoom(19);
      } else {
        StembureausApp.map.addLayer(osm);
        StembureausApp.map.setMaxZoom(18);
      }

      // Show BRT only when zoomed in on European Netherlands, use OSM for
      // the rest
      StembureausApp.map.on('zoom move', function() {
        var zoom = StembureausApp.map.getZoom();
        var center = StembureausApp.map.getCenter();
        if (zoom >= 7 && center.lat > 50 && center.lat < 54 && center.lng > 3 && center.lng < 8) {
          StembureausApp.map.removeLayer(osm);
          StembureausApp.map.addLayer(brt);
          chooseLayers.addTo(StembureausApp.map);
          StembureausApp.map.setMaxZoom(19);
        } else {
          chooseLayers.remove(StembureausApp.map);
          StembureausApp.map.removeLayer(brt);
          StembureausApp.map.removeLayer(hwh);
          StembureausApp.map.addLayer(osm);
          StembureausApp.map.setMaxZoom(18);
        }
      });

      // Initialize the filters
      var filters = {
        //'dag': $('#dag-filter').val(),
        'openingstijden': $('#openingstijden-filter').val(),
        'toegankelijk': $('.toegankelijk-filter').val(),
        'visuele-hulpmiddelen': $('.visuele-hulpmiddelen-filter').val(),
        'auditieve-hulpmiddelen': $('.auditieve-hulpmiddelen-filter').val(),
        'gehandicapten': $('.gehandicapten-filter').val(),
        'akoestiek': $('.akoestiek-filter').val(),
      };

      // The toegankelijkheidsfilter fields exist twice because of
      // responsiveness (one is always hidden); make sure that both fields
      // have the same value when one of them is changed.
      $(".toegankelijk-filter").change(function() {
        $(".toegankelijk-filter").val($(this).val());
      });

      $(".visuele-hulpmiddelen-filter").change(function() {
        $(".visuele-hulpmiddelen-filter").val($(this).val());
      });

      $(".auditieve-hulpmiddelen-filter").change(function() {
        $(".auditieve-hulpmiddelen-filter").val($(this).val());
      });

      $(".gehandicaptentoilet-filter").change(function() {
        $(".gehandicaptentoilet-filter").val($(this).val());
      });

      $(".akoestiek-filter").change(function() {
        $(".akoestiek-filter").val($(this).val());
      });

      // Apply updates to the map if a filter is clicked
      $('.filter').change(function() {
        //filters['dag'] = $('#dag-filter').val();
        filters['openingstijden'] = $('#openingstijden-filter').val();
        filters['toegankelijk'] = $('.toegankelijk-filter').val();
        filters['visuele-hulpmiddelen'] = $('.visuele-hulpmiddelen-filter').val();
        filters['auditieve-hulpmiddelen'] = $('.auditieve-hulpmiddelen-filter').val();
        filters['gehandicaptentoilet'] = $('.gehandicaptentoilet-filter').val();
        filters['akoestiek'] = $('.akoestiek-filter').val();

        StembureausApp.filter_map(filters);
        // Only run this on gemeente pages, which show stembureaus in the
        // 'form-search' list
        if (document.getElementById('form-search')) {
            StembureausApp.search(get_query());
        }
      });

      // Default view: based on which option is selected by default in map.html
      StembureausApp.filter_map(filters);

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
    }

    if ($('#map').length) {
      run_stembureaus();
    }
  },
  // JavaScript to be fired on pages that contain the map, after the init JS
  finalize() {
    $('#nlmaps-geocoder-control-input').attr('placeholder', 'Zoeken (bv. straat of postcode)');
  },
};
