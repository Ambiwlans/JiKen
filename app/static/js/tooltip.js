$(function () {
    var pred = parseInt($('.predmin').text() || 0);
    
    console.log(pred);
    
    if (pred > 0 && pred < 100)
    {
        $('.predmain').attr("title", "You're not quite ready for JLPT");
    }
    else if (pred < 300)
    {
        $('.predmain').attr("title", "You're ready for JLPT level N5!");
    }
    else if (pred < 650)
    {
        $('.predmain').attr("title", "You're ready for JLPT level N4!");
    }
    else if (pred < 1000)
    {
        $('.predmain').attr("title", "You're ready for JLPT level N3!");
    }
    else if (pred < 2000)
    {
        $('.predmain').attr("title", "日本語能力試験N2!");
    }
    else
    {
        $('.predmain').attr("title", "日本語能力試験N1!");
    }
    
    if (pred > 80 && pred < 240)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>Could challenge Kanji Kentei level 10 with study.");
    }
    else if (pred < 440)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>Could challenge Kanji Kentei level 9 with study.");
    }
    else if (pred < 640)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>Could challenge Kanji Kentei level 8 with study.");
    }
    else if (pred < 825)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>Could challenge Kanji Kentei level 7 with study.");
    }
    else if (pred < 1006)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>Could challenge Kanji Kentei level 6 with study.");
    }
    else if (pred < 1300)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検５級挑戦できます！");
    }
    else if (pred < 1600)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検4級挑戦できます！");
    }
    else if (pred < 1950)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検3級挑戦できます！");
    }
    else if (pred < 2136)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検準2級挑戦できます！");
    }
    else if (pred < 2965)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検2級挑戦できます！");
    }
    else if (pred < 6355)
    {
        $('.predmain').attr("title", $('.predmain').attr("title") + "<br>書けて頑張れば、漢検準1級挑戦できます！");
    }
    else
    {
        $('.predmain').attr("title", "漢字王!");
    }
    
    //Easter egg
    if (pred > 1500)
    {
        $('.footer-content').html("<a href='https://github.com/Ambiwlans'>Ambiwlans</a>自作。気に入ったら、ガチに広めてください！");
    }
    $('[data-toggle="tooltip"]').tooltip();
});