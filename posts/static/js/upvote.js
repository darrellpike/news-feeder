$(function () {
   // Upvote button
    $(document).on('click touch', '.article .btn-upvote', function (e) {
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
                var currentRatingNumber = rating_number.context.innerText;
                if (vote === 'upvote') {
                    if (!(currentRatingNumber.indexOf('k') !== -1)) {
                        rating_number.html(parseInt(currentRatingNumber) + 1);
                    }
                    button.addClass('active');
                } else if (vote === 'unvote') {
                    if (!(currentRatingNumber.indexOf('k') !== -1)) {
                        rating_number.html(parseInt(currentRatingNumber) - 1);
                    }
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