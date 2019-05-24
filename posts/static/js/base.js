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
    let searchInput = $('#search-input');

    $('.open-another-modal').on('click touch', function () {
        let target = $($(this).data('target'));
        if (target.length) {
            $(this).parents('.modal').modal('hide');
            setTimeout(function () {
                target.modal('show');
            }, 600)
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

    $('.modal').on('shown.bs.modal', function () {
        if ($(window).width() > 768) $(this).find('input:not(input[type="hidden"])').focus();
    });

    $(document).on('click touch', '.article .article-title, .article .article-comments', function (e) {
        let width = $(window).width();
        if (width > 768) {
            e.preventDefault();
            let article = $(this).closest('.article');
            let slug = article.data('article');
            let first = Boolean(article.data('first'));
            let last = Boolean(article.data('last'));

            $.ajax({
                type: 'GET',
                url: '/post/' + slug,
                success: function (html) {
                    let modal = $('#PostModal');
                    modal.find('.modal-content').html(html);
                    if (first) {
                        modal.find('.previous-article').hide();
                    } else if (last) {
                        modal.find('.next-article').hide();
                    }
                    modal.find('.article').data('latest', article.data('latest'));
                    modal.find('.article').data('search', article.data('search'));
                    modal.modal('show');
                },
                error: function (data, textStatus) {
                    console.log(data, textStatus);
                }
            });
        }
    });

    $(document).on('click touch', '.previous-article, .next-article', function () {
        let button = $(this);
        let articleId = button.siblings('.article').data('article');
        let articleInList;
        let article;
        let latest = Boolean(button.siblings('.article').data('latest'));
        let searchResults = Boolean(button.siblings('.article').data('search'));
        if (latest) {
            articleInList = $('.latest-news .article[data-article="' + articleId + '"]');
        } else if (searchResults) {
            articleInList = $('.search-results .article[data-article="' + articleId + '"]');
        } else {
            articleInList = $('.news .article[data-article="' + articleId + '"]');
        }
        let clickOnButton = true;

        if (button.hasClass('next-article')) {
            article = articleInList.next('.article');
        } else if (button.hasClass('previous-article')) {
            article = articleInList.prev('.article');
        } else {
            console.error("Button doesn't have class.");
        }
        let modal = button.parents('#PostModal');
        modal.modal('hide');
        modal.on('hidden.bs.modal', function () {
            if (clickOnButton) {
                article.find('.article-title').click();
            }
            clickOnButton = false;
        });
    });

    var searchOpened = false;

    searchButton.click(function () {
        search.animate({height: 'toggle'}, 250);
        if (!searchOpened) {
            searchInput.focus();
            searchOpened = true;
        } else searchOpened = false;

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


function focusAndOpenKeyboard(el, timeout) {
  if(!timeout) {
    timeout = 100;
  }
  if(el) {
    // Align temp input element approximately where the input element is
    // so the cursor doesn't jump around
    var __tempEl__ = document.createElement('input');
    __tempEl__.style.position = 'absolute';
    __tempEl__.style.top = (el.offsetTop + 7) + 'px';
    __tempEl__.style.left = el.offsetLeft + 'px';
    __tempEl__.style.height = 0;
    __tempEl__.style.opacity = 0;
    // Put this temp element as a child of the page <body> and focus on it
    document.body.appendChild(__tempEl__);
    __tempEl__.focus();

    // The keyboard is open. Now do a delayed focus on the target element
    setTimeout(function() {
      el.focus();
      el.click();
      // Remove the temp element
      document.body.removeChild(__tempEl__);
    }, timeout);
  }
}

function goToByScroll(id) {
    // Remove "link" from the ID
    $('html,body').animate({
        scrollTop: $("#" + id).offset().top
    }, 'slow');
}