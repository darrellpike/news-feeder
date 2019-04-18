$(function () {
	// $('.article .btn-upvote').click(function (e) {
	// 	e.preventDefault();
	// 	$.ajax({
	// 		url: "{% url 'vote_post' %}",
    //
	// 	})
    // });

    let searchInput = $('#search-form input');
    let suggestNewsButton = $('.suggest-news');
    searchInput.focus(function () {
        suggestNewsButton.fadeTo('fast', 0);
        suggestNewsButton.hide();
    });

    searchInput.focusout(function () {
        setTimeout(function () {
            suggestNewsButton.show();
            suggestNewsButton.fadeTo('fast', 1);
        }, 400)
    });


    $('.article .article-title').on('click', function () {
        let url = $(this).closest('.article').data('url');
        // $.ajax({
        //     type: 'GET',
        //     url: url,
        //     success: function (html) {
        //         let modal = $('#PostModal');
        //         modal.find('.modal-content').html(html);
        //         modal.modal('show');
        //     },
        //     error: function (data, textStatus) {
        //         console.log(data, textStatus);
        //     }
        // });
    });
});
