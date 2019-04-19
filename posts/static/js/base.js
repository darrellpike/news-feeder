$(function () {
    let search = $('#search-form');
    let searchButton = $('.btn-search');
    let searchInput = $('#search-form input');
    searchButton.click(function () {
        search.animate({height: 'toggle'}, 250, function () {
            searchInput.focus();
        });
        if (search.css('display') !== 'none') {
            $('.main-content').css('display', 'block');
            $('#search-results').css('display', 'none');
        }
    });

    function searchSend(str, pageNumber=1) {
        $.ajax({
            method: 'GET',
            url: '/search/',
            data: {'q': str, 'page': pageNumber},
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
    let pageNumber = 1;
    $('#search-results').on('click', '.btn-pagination', function (e) {
        let next_page = $(this).data('page');
        searchSend(searchInput.val(), next_page);
    });

    search.on('submit', function (e) {
        e.preventDefault();
        searchSend(event.target.querySelector('input').value, pageNumber);
    });

    searchInput.on('keyup', function (e) {
        clearTimeout(timeoutID);
      timeoutID = setTimeout(() => searchSend(e.target.value, pageNumber), 250);
    });
});
