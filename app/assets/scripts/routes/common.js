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
      $('#bag-results').empty();
      var output = '<ul>';
      console.dir(data);
      $.each(data, function (idx, elem) {
        output += '<li>' + elem.openbareruimte + ' ' + elem.huisnummer + ' ' + elem.huisnummertoevoeging + '</li>';
      });
      output += '</ul>';
      $('#bag-results').html($(output));
    }, 'json');
  }, 200));
};
