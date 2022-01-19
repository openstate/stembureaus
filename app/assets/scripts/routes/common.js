import clickmap from './clickmap';

export default {
  init() {
    // JavaScript to be fired on all pages
    console.log('javascript common loaded!');
    // JavaScript to be fired on pages that contain the map
    if ($('.edit-form').length) {
      run_editform();
    }

    clickmap.init();
  },
  finalize() {
    // JavaScript to be fired on all pages, after page specific JS is fired
    clickmap.finalize();
  },
};

var run_editform = function () {
  // https://stackoverflow.com/questions/1909441/how-to-delay-the-keyup-handler-until-the-user-stops-typing
  function delay(callback, ms) {
    var timer = 0;
    return function() {
      var context = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        callback.apply(context, args);
      }, ms || 0);
    };
  }

  console.log('attaching to edit form now!');
  $('#adres_stembureau').on('keyup', delay(function (e) {
    var query = $(this).val();

    if (query.length < 1) {
      $('#bag-results').empty();
      console.log('query not long enough');
      return;
    }

    $('#bag-results').prepend($('<ul class="loading-list"><li><div class="loading"></div></li></ul>'));
    delay(console.log('loading'), 3000);
    $.get('/t/' + encodeURIComponent(query), function (data) {
      var attrs_as_data = ['nummeraanduiding', 'lat', 'lon', 'x', 'y'];
      var attrs_conversions = {
        nummeraanduiding: 'bag_nummeraanduiding_id',
        lat: 'latitude',
        lon: 'longitude',
        x: 'x',
        y: 'y'
      }
      var output = '<ul>';
      console.dir(data);
      if (query == '0000000000000000') {
        output += '<li><a href="javascript:void(0);"';
        output += ' data-nummeraanduiding="0000000000000000"'
        output += ' data-lat="' + StembureausApp.bag_record.lat + '"';
        output += ' data-lon="' + StembureausApp.bag_record.lon + '"';
        output += ' data-x="' + StembureausApp.bag_record.x + '"';
        output += ' data-y="' + StembureausApp.bag_record.y +'">0000000000000000 (geen adres beschikbaar in de BAG; kies deze optie voor Bonaire, Sint Eustatius en Saba)</a></li>';
      } else {
        $.each(data, function (idx, elem) {
          output += '<li><a href="javascript:void(0);"';
          attrs_as_data.forEach(function (a) {
            output += ' data-' + a +'="' + elem[a] + '"';
          });
          output += '>' + elem.openbareruimte + ' ' + elem.huisnummer +elem.huisletter;
          if (elem.huisnummertoevoeging != '') {
            output += '-' + elem.huisnummertoevoeging;
          }
          output += ' (' + elem.woonplaats + ') [' + elem.nummeraanduiding + ']';
          output += '</a></li>';
        });
      }
      output += '</ul>';
      $('#bag-results .loading-list').remove();
      $('#bag-results').html($(output));
      $('#bag-results ul li a').on('click', function (e) {
          e.preventDefault();
          console.log('li clicked!');
          var adres = $(this).text();
          var clicked_elem = $(this);
          $('#adres_stembureau').val($(this).text());
          var all_empty = true;
          var should_replace = true;
          attrs_as_data.forEach(function (a) {
            all_empty = all_empty && ($('#' + attrs_conversions[a]).val() == '');
          });
          if (!all_empty) {
            if (window.confirm("Wilt u de al ingevulde coördinaten (Latitude/Longitude en X/Y) van het stembureau automatisch laten bijwerken naar die van het geselecteerde adres?")) {
              should_replace = true;
            } else {
              should_replace = false;
            }
          }
          if (should_replace) {
            attrs_as_data.forEach(function (a) {
              console.log('updating attribute : ' + a + ' => ' + attrs_conversions[a] + ' : ' + clicked_elem.attr('data-'+a));
              $('#' + attrs_conversions[a]).val(clicked_elem.attr('data-'+a));
            });
          }
          // Always replace the BAG Nummeraanduiding ID with the one belonging to the newly selected address
          $('#bag_nummeraanduiding_id').val(clicked_elem.attr('data-nummeraanduiding'));

          $('#bag-results').empty();
          $(document).trigger('stm:address');
          return false;
      });
    }, 'json');
  }, 200));
};
