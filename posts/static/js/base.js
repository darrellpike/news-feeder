$(function () {
    var csrftoken = Cookies.get('csrftoken');
    let search = $('.search-container');
    let searchButton = $('.btn-search');
    let searchInput = $('#search-form input');

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

    searchButton.click(function () {
        search.animate({height: 'toggle'}, 250, function () {
            searchInput.focus();
        });
        if (search.css('display') !== 'none') {
            $('.main-content').css('display', 'block');
            $('#search-results').css('display', 'none');
        }
    });


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

    $(document).on('submit', '.form', function (e) {
        e.preventDefault();
        var form = $(this);
        $('.error-text').html('');
        $('.input-with-label').removeClass('error');

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
            success: function (data) {
                window.location.href = data.url;
            },
            error: function (data) {
                var errors;
                if (data.statusText === "Unprocessable Entity"){
                    errors = $.parseJSON(data.responseText);
                } else if (data.status === 500) {
                    errors = {"__all__": data.statusText};
                }
                for (error in errors) {
                    if (errors.hasOwnProperty(error)) {
                        if (error === '__all__') {
                            $('#non-field').html(errors[error]);
                        } else {
                            var input = $('input[name=' + error + ']');
                            input.closest('.input-with-label').find('.error-text').html(errors[error]);
                            input.closest('.input-with-label').addClass('error');
                        }
                    }
                }
            }
        });
    });
});

jQuery.fn.preventDoubleSubmit = function() {
    jQuery(this).submit(function() {
        console.log(this.beenSubmitted);
        if (this.beenSubmitted) {
            return false;
        }
        else {
            this.beenSubmitted = true;
        }
    });
};
