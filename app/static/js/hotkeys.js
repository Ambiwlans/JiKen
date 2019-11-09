function flip(){
    if ($(".flipped")[0])
    {
        $(".flipped").removeClass("flipped");
    }
    else
    {
        $(".flashcard").addClass("flipped");
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
        case 40:    // Pressing down or space, flip card
        case 32:
            e.preventDefault();
            flip();
            break;
    }
}
