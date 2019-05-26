$(function () {
    // New comment in reply
    $(document).on('click touch', '.comment-reply-btn', function (e) {
        let replySection = $(this).parent().siblings('.comment-reply-new');
        replySection.animate({height: 'toggle'}, 450, function () {
            if (replySection.attr('aria-expanded') === 'false') {
                replySection.attr('aria-expanded', 'true');
                replySection.find('textarea').focus();
            } else replySection.attr('aria-expanded', 'false');
        });
        if (replySection.attr('aria-expanded') === 'false') {
            replySection.find('textarea').focus();
        }
    });

    $(document).on('click touch', '.article-new-comment button[type="reset"]', function (e) {
        let replySection = $(this).parents('.comment-reply-new');
        replySection.animate({height: 'toggle'}, 450, function () {
            replySection.attr('aria-expanded', 'false');
        });
    });

    // New comment
    $('#newCommentForm').preventDoubleSubmit();
    $(document).on('submit', '.newCommentForm', function (e) {
        e.preventDefault();
        let form = $(this);
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: form.serialize(),
            success: function (data) {
                this.beenSubmitted = false;
                let commentSection;
                let newComment;
                let reply = form.parents('.comment-reply-new');
                let is_article_comment = form.siblings('.article-comments-body').length;
                if (is_article_comment) {
                    commentSection = $('.article-comments-body');
                    newComment = commentSection.append(data);
                    newComment.animate({height: 'toggle'}, 450);
                }
                else if (reply.length) {
                    commentSection = reply.siblings('.comment-children');
                    commentSection.prepend('<div class="comment-child"></div>');
                    newComment =  commentSection.find('>.comment-child:first-of-type').append(data).find('.comment');
                    reply.animate({height: 'toggle'}, 450, function () {
                        newComment.animate({height: 'toggle'}, 450);
                    });
                }
                let article_id = form.parents('.article-comments').siblings('.article').data('article');
                let currentCommentNumber = $('.comments-count span');
                let newCommentNumber = parseInt(currentCommentNumber.html()) + 1;
                currentCommentNumber.html(newCommentNumber);
                $('.article[data-article="' + article_id + '"] .article-comments-text span').html(newCommentNumber);
                $(this).find('textarea').val('');
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
            }
        });
    });
    // Sorting
    $(document).on('click touch', '.comment-sorting button', function () {
        let button = $(this);
        let url = button.data('sort');
        $.ajax({
            type: 'GET',
            url: url,
            success: function (data) {
                button.parents('.article-comments').find('.article-comments-body').html(data);
                button.parent().find('.active').removeClass('active');
                button.addClass('active');
            }
        })

    });
});