
$(document).ready(function() {
	options = { placement: 'right',
		    html: true,
	};
	$('.vote').eq(2).popover(options);
	$('.vote').eq(2).popover('show');
	$('#upvote-ok').click(function() {
		$('.vote').eq(2).popover('hide');
		_gaq.push(['_trackEvent', 'Actions', 'Upvote Instructions OK', 'Clicked OK on first-visit popover instruction of upvote arrow.']);
	    });
    });

