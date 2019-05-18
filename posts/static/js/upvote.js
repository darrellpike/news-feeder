$(function () {
   // Upvote button
    $(document).on('click touch', '.btn-upvote', function (e) {
        var rating_number = $(this).find('.rating-text');
        var button = $(this);
        $.ajax({
            method: 'POST',
            url: button.data('vote'),
            data: {
                'csrfmiddlewaretoken': Cookies.get('csrftoken'),
            },
            success: function (vote) {
                if (button.hasClass('modal-article-vote')) {
                    let article = button.parents('.article').data('article');
                    button = $('.article[data-article="' + article + '"]').find('.btn-upvote');
                    rating_number = button.find('.rating-text');
                }
                if (vote['up_vote']) {
                    rating_number.html(vote['score']);
                    button.addClass('active');
                } else {
                    rating_number.html(vote['score']);
                    button.removeClass('active');
                }
            },
            error: function (err) {
                console.log(err);
            }
        });
    });
});