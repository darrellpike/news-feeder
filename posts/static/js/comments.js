$(function () {
    $('#newCommentForm').preventDoubleSubmit();
    $(document).on('submit', '#newCommentForm', function (e) {
        e.preventDefault();
        let form = $(this);
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: form.serialize(),
            success: function (data) {
                this.beenSubmitted = false;
                let commentSection = $('.article-comments-body');
                let article_id = form.parents('.article-comments').siblings('.article').data('article');
                commentSection.append(data);
                commentSection.find('.comment:last-of-type').show('slow');
                let currentCommentNumber = $('.comments-count span');
                let newCommentNumber = parseInt(currentCommentNumber.html()) + 1;
                currentCommentNumber.html(newCommentNumber);
                $('.article[data-article="' + article_id + '"] .article-comments-text span').html(newCommentNumber);
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
                            var input = $('textarea[name=' + error + ']');
                            input.closest('.input-group').find('.error-text').html(errors[error]);
                            input.closest('.input-group').addClass('error');
                    }
                }
                console.log(data);
            }
        });
    });
});