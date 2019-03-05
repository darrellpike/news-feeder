$(document).ready(function() {
	$('.email-share').click(function() {
		var post_id = $(this).attr("post_id");
		$('#id_post_id_modal').attr("value",post_id);
	    });
    });

$(document).ready(function() {
	$('.flag-post').click(function() {
		var post_id = $(this).attr("post_id");
		$('#flag-post-'+post_id).submit();
	    });

	$('#register-modal').on('hidden.bs.modal', function () {
		$('#upvote-register-explanation').hide();
	    })
    });