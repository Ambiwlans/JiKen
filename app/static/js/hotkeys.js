function flip(){
    if ($(".flipped")[0])
    {
        $(".flipped").removeClass("flipped");
        $(".btn-group.front").show()
        $(".btn-group.back").hide()    
    }
    else
    {
        $(".flashcard").addClass("flipped");
        $(".btn-group.front").hide()
        $(".btn-group.back").show()
    }
}
document.onkeydown=function(e){
    switch(e.which){
        case 37:    // Pressing left, click 'know' button
            window.location.href = $("#know").attr("href");
            break;
        case 39:    // Pressing right, click 'dunno' button
            window.location.href = $("#dunno").attr("href"); 
            break;
        case 40:    // Pressing up, down or space, flip card
        case 38:
        case 32:
            e.preventDefault();
            flip();
            break;
    }
}
