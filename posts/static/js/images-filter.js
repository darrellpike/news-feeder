window.onload = function () {
    function setMoreURL(href, rel) {
	    $('#image-list > .items > .endless_container').remove();//attr('href',url);
	    $('#image-list > .items').append('<div class="endless_container"><a class="endless_more" href="'+href+'" rel="'+rel+'">more</a><div class="endless_loading" style="display: none;">loading</div></div>')
    }
    function clearImages() {
	    $('.instagram-image').remove();
	    $('[data-toggle="lightbox"]').remove();
    }
    $(".images-filter").click(function() {
	    var next = $(this).next();
	    if(next.length==0) {
	        next = $(this).siblings().first();
	    }
	    next.show();
	    next.siblings().hide();
        
	    next.addClass("btn-primary");
	    next.removeClass("btn-default");
	    next.siblings().addClass("btn-default");
	    next.siblings().removeClass("btn-primary");
        
	    
	    clearImages();
	    var ref = next.attr("filter_ref");
	    console.log(ref);
	    setMoreURL("/"+ref+"/?images_page=0", "images_page");
	    $('#image-list > .items > .endless_container > .endless_more').click();
    });
    
    
    function setStoriesMoreURL(href, rel) {
	    $('#story-list > .items > .endless_container').remove();//attr('href',url);
	    $('#story-list > .items').append('<div class="endless_container"><a class="endless_more" href="'+href+'" rel="'+rel+'">more</a><div class="endless_loading" style="display: none;">loading</div></div>')
    }
    function clearStories() {
	    $('.post-numbers').remove();
	    $('.post').remove();
    }
    $(".stories-filter").click(function() {
	    var next = $(this).next();
	    if(next.length==0) {
	        next = $(this).siblings().first();
	    }
	    next.show();
	    next.siblings().hide();
        
	    next.addClass("btn-primary");
	    next.removeClass("btn-default");
	    next.siblings().addClass("btn-default");
	    next.siblings().removeClass("btn-primary");
	    
	    clearStories();
	    var ref = next.attr("filter_ref");
	    setStoriesMoreURL("/"+ref+"/?page=0", "page");
	    $('#story-list > .items > .endless_container > .endless_more').click();
    });
};
