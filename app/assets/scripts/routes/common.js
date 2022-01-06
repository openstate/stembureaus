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
  console.log('attaching to edit form now!');
  $('#bag_nummeraanduiding_id').on('keyup', function (e) {
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
  });
};
