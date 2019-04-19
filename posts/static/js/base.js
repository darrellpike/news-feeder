$(function () {
    var csrftoken = Cookies.get('csrftoken');
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

    // Upvote button
    $(document).on('click', '.article .btn-upvote', function (e) {
        var rating_number = $(this).find('.rating-text');
        var button = $(this);
        $.ajax({
            method: 'POST',
            url: '/vote_post/',
            data: {
                'csrfmiddlewaretoken': csrftoken,
                'post': button.parents('.article').data('article')
            },
            success: function (vote) {
                if (vote === 'upvote') {
                    rating_number.html(parseInt(rating_number.context.innerText) + 1);
                    button.addClass('active');
                } else if (vote === 'unvote') {
                    rating_number.html(parseInt(rating_number.context.innerText) - 1);
                    button.removeClass('active');
                } else {
                    console.log(vote);
                }
            },
            error: function (err) {
                console.log(err);
            }
        });
    });
});
