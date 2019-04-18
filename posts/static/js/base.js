$(function () {
    let search = $('#search-form');
    let searchButton = $('.btn-search');
    searchButton.click(function () {
        search.animate({height: 'toggle'}, 250, function () {
            search.children().focus();
        });
        if (search.css('display') !== 'none') {
            $('.main-content').css('display', 'block');
            $('#search-results').css('display', 'none');
        }
    });

    function searchSend(str) {
        $.ajax({
            method: 'GET',
            url: '/search/',
            data: {'q': str},
            success: function (html) {
                $('.main-content').css('display', 'none');
                $('#search-results').html(html).css('display', 'block');
            },
            error: function (err) {
                console.log(err);
            }
        });
    }

    var timeoutID = null;
    $('#search-form input').on('keyup click', function (e) {
        clearTimeout(timeoutID);
      timeoutID = setTimeout(() => searchSend(e.target.value), 250);
    });
});
