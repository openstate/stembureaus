export default {
  init() {
    // JavaScript to be fired on all pages
    console.log('javascript common loaded!');
    // JavaScript to be fired on pages that contain the map
    if ($('.edit-form').length) {
      run_editform();
    }

  },
  finalize() {
    // JavaScript to be fired on all pages, after page specific JS is fired
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

    if (query.length < 3) {
      console.log('query not long enough');
      return;
    }

    $.get('/t/' + encodeURIComponent(query), function (data) {
      var attrs_as_data = ['nummeraanduiding', 'lat', 'lon', 'x', 'y'];
      var attrs_conversions = {
        nummeraanduiding: 'bag_nummeraanduiding_id',
        lat: 'latitude',
        lon: 'longitude',
        x: 'x',
        y: 'y'
      }
      $('#bag-results').empty();
      var output = '<ul>';
      console.dir(data);
      $.each(data, function (idx, elem) {
        output += '<li><a href="javascript:void(0);"';
        attrs_as_data.forEach(function (a) {
          output += ' data-' + a +'="' + elem[a] + '"';
        });
        output += '>' + elem.openbareruimte + ' ' + elem.huisnummer;
        if (elem.huisnummertoevoeging != '') {
          output += '-' + elem.huisnummertoevoeging;
        }
        output += ' (' + elem.woonplaats + ')';
        output += '</a></li>';
      });
      output += '</ul>';
      $('#bag-results').html($(output));
      $('#bag-results ul li a').on('click', function (e) {
          e.preventDefault();
          console.log('li clicked!');
          var adres = $(this).text();
          var clicked_elem = $(this);
          $('#adres_stembureau').val($(this).text());
          //$('#bag_nummeraanduiding_id').val($(this).attr('data-nummeraanduiding'));
          attrs_as_data.forEach(function (a) {
            console.log('updating attribute : ' + a + ' => ' + attrs_conversions[a] + ' : ' + clicked_elem.attr('data-'+a));
            if ($('#' + attrs_conversions[a]).val() == '') {
              $('#' + attrs_conversions[a]).val(clicked_elem.attr('data-'+a));
            }
          });
          $('#bag-results').empty();
          return false;
      });
    }, 'json');
  }, 200));
};
