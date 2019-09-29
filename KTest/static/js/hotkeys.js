document.onkeydown=function(e){
    if(e.which == 37)   // Pressing left, click 'know' button
    {
        window.location.href = $("#know").attr("href"); 
    }
    if(e.which == 39)   // Pressing right, click 'dunno' button
    {
        window.location.href = $("#dunno").attr("href"); 
    }
    if(e.which == 40)   // Pressing down, flip card
    {
   
    }
}