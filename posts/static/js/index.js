$(document).ready(function() {
    function viewJustStories() {
        $(".story-row").removeClass("hidden");
        $(".instagram-image-row").addClass("hidden");
    }
    function viewJustImages() {
        $(".story-row").addClass("hidden");
        $(".instagram-image-row").removeClass("hidden");
    }
    function viewBoth() {
        $(".story-row").removeClass("hidden");
        $(".instagram-image-row").removeClass("hidden");
    }
    $(".view-just-stories").click(viewJustStories);
    $(".view-just-images").click(viewJustImages);
    $(".view-both").click(viewBoth);
    $("li.navbar-sort-tab").click(function() {
        $(this).siblings().removeClass("active");
        $(this).addClass("active");
    });
});
