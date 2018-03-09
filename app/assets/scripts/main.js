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

var StembureausApp = window.StembureausApp || {stembureaus: []};

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
    $('#results-search').append($(
      '<div class="result">' +
      '<h2 class="pull-left"><a href="/s/' + matches[i]['Gemeente'] + '/' + matches[i]['UUID'] + "\">" + matches[i]['Straatnaam'] + ' ' + matches[i]['Huisnummer'] + matches[i]['Huisnummertoevoeging'] + '</a></h2>' +
      '<p class="pull-right">' + weelchair_labels[matches[i]["Mindervaliden toegankelijk"]] + '</p>' +
      '<h5><a href="/s/' + matches[i]['Gemeente'] + '">' + matches[i]['Plaats'] + '</a></h5>' +
      '<p>' + opinfo[0].split('T')[1].slice(0, 5) + ' &dash; ' + opinfo[1].split('T')[1].slice(0, 5) + '</p>' +
      '</div>'
    ))
  }

  if (matches.length == 0) {
    $('#results-search').append($('<p>Helaas, we hebben niks kunnen vinden. Dit komt waarschijnlijk omdat we alleen zoeken in de lijst van stembureaus, en niet in alle straten. Wilt U weten welk stembureau het dichstbij U in de buurt is? Gebruik dan de knop \'Gebruik mijn locatie\'.</p>'));
  }
};

StembureausApp.search = function (query) {
  console.log('should be searching for : [' + query + '] now ...');
  console.log(query.split(/\s+/));
  var stembureau_matches = StembureausApp.fuse.search(query);
  console.log('matches:');
  console.dir(stembureau_matches);

  StembureausApp.show(stembureau_matches);
};

StembureausApp.init = function() {
  console.log('init!');
  console.log('one more test ....');

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

  $('#form-search').submit(function (e) {
    e.preventDefault();
    return false;
  });

  $('#form-search input[type="text"]').keyup(function (e) {
    StembureausApp.search($(this).val());
  });

  $('#btn-location').click(function (e) {
    StembureausApp.map.locate({setView : true});
    return false;
  });
};


$(document).ready(function () {
  StembureausApp.init();
});
