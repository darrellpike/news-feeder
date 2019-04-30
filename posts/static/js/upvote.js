$(function () {
   // Upvote button
    $(document).on('click', '.article .btn-upvote', function (e) {
        var rating_number = $(this).find('.rating-text');
        var button = $(this);
        $.ajax({
            method: 'POST',
            url: '/api/vote_post/',
            data: {
                'csrfmiddlewaretoken': Cookies.get('csrftoken'),
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