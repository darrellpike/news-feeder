jQuery.fn.preventDoubleSubmit = function() {
    jQuery(this).submit(function() {
        if (this.beenSubmitted) {
            return false;
        }
        else {
            this.beenSubmitted = true;
        }
    });
};


$(function () {
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

    $(document).on('click touch', '.article .article-title, .article .article-comments', function (e) {
        let width = $(window).width();
        if (width > 768) {
            e.preventDefault();
            let slug = $(this).closest('.article').data('article');
            $.ajax({
                type: 'GET',
                url: '/post/' + slug,
                success: function (html) {
                    let modal = $('#PostModal');
                    modal.find('.modal-content').html(html);
                    modal.modal('show');
                },
                error: function (data, textStatus) {
                    console.log(data, textStatus);
                }
            });
        }
    });

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

    $(document).on('click touch', 'form input, form textarea', function () {
       this.form.beenSubmitted = false;
       $(this).parent().removeClass('error');
       $(this).siblings('.error-text').html('');
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
                this.beenSubmitted = false;
                window.location.href = data.url;
            },
            error: function (data) {
                this.beenSubmitted = false;
                var errors;
                if (data.status === 422){
                    errors = $.parseJSON(data.responseText);
                } else if (data.status === 500) {
                    errors = {"__all__": data.statusText};
                }
                for (error in errors) {
                    if (errors.hasOwnProperty(error)) {
                        if (error === '__all__') {
                            let error_text = errors[error];
                            if (error_text[0] === 'This account is inactive.') {
                                let email = form.find('#id_email').val();
                                error_text += ' <a class="btn-link" href="/accounts/activate/send_again/' + email + '/">Send activation email again?</a>';
                            }
                            $('#non-field').html(error_text);
                        } else  {
                            var input = $('input[name=' + error + ']');
                            input.closest('.input-with-label').find('.error-text').html(errors[error]);
                            input.closest('.input-with-label').addClass('error');
                        }
                    }
                }
            }
        });
    });

    $('#register_form').preventDoubleSubmit();
        $(document).on('submit', '#register_form', function (e) {
            e.preventDefault();
            let register_form = $(this);
            $('.error-text').html('');
            $('.input-with-label').removeClass('error');
            $.ajax({
                method: 'POST',
                url: register_form.attr('action'),
                data: register_form.serialize(),
                success: function (data) {
                    register_form.beenSubmitted = false;
                    register_form.html(data);
                },
                error: function (data) {
                    register_form.beenSubmitted = false;
                    let errors = $.parseJSON(data.responseText);
                    for (error in errors) {
                        if (errors.hasOwnProperty(error)) {
                            var input = $('input[name=' + error + ']');
                            input.closest('.input-with-label').find('.error-text').html(errors[error]);
                            input.closest('.input-with-label').addClass('error');
                        }
                    }
                }
            });
        });
});