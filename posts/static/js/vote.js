
$(document).ready(function() {
	$('.vote').click(function() {
		//alert('post='+$(this).attr("item_id")+"&score="+$(this).attr("score"));
		var score = $(this).attr("score");
		var id = $(this).attr("item_id");
		if(!id) {
		    $('#register-modal').modal();
		    return;
		}
		var vote_url = "/vote_"+$(this).attr("vote_type")+"/";

		var postdata = {
		    'csrfmiddlewaretoken': csrfmiddlewaretoken,
		    'score': score,
		    'post': id,
		    'comment': id,
		};
		$.post(vote_url, postdata);
		$(this).hide();
		$(this).siblings().hide();
		var score_id = "#" + id + "-score";
		var new_score = parseInt($(score_id).html())+parseInt(score);
		$(score_id).html(new_score);
	    });
    });


$(document).ready(function() {
	//$('.vote').tooltip()
    });

