# JiKen

[JiKen](https://jiken.herokuapp.com/) is a simple kanji quiz that uses statistics and machine learning to accurately and quickly predict a user's knowledge level. I always found it tedious to get a good read of my current kanji level while studying using existing tests which either take forever or are terribly innaccurate so I made this.

The name JiKen is a bit of a play on words/kanji. It could be read as 字検 (letter test, similar to 漢検 the infamous official kanji test) or 事件 (incident). I left it in romaji for the ambiguity. KTest was just a working title, and kind of lame.

## Host/Location

# https://jiken.herokuapp.com/
* Using Heroku as a webhost, ClearDB for MySQL, HerokuRedis for sessions.

## Math

First thing to know to understand why this works so well is that kanji usage (and recognition) is not flat/random but has a relatively normal distribution and follows [Ziph's Law](https://en.wikipedia.org/wiki/Zipf%27s_law). This allows us to make relatively sensible predictions of people's knowledge using a sigmoid function.

There are two main algorithms worth noting. 

One predicts how many kanji you know (the graph) based on your answers. This is a Nelder-Mead regression algo with custom regularization: giving a lot of weight to the initial weights (safe assumption until data is collected), L2 reg (to avoid traps), some penalty to change between questions to give users a smooth experience. I also do bias correction as per https://cs.nyu.edu/~mohri/pub/bias.pdf since the questions selected are not random. No formal tuning methods were use, everything was done by hand until it felt good (the tuning target was to meet user expectations rather than simply being mathematically accurate).

The other algorithm ranks the difficulty of every kanji for future testing. If 100 people know "馬" but don't know "鹿" then the algorithm will shuffle the ranks around so that "鹿" is ranked lower, "馬" higher. This is called a Learning to rank algorithm: https://mlexplained.com/2019/05/27/learning-to-rank-explained-with-code/. Of course, this was again made more complicated by having biased sample selection.

## Built With

* Flask
* SQLAlchemy (MySQL)
* Redis (for sessions/ buffering)
* APscheduler
* Bootstrap
* ChartJS


## Contact/Bugs

You can report bugs here or contact me via [reddit](https://www.reddit.com/message/compose?to=%2Fu%2FAmbiwlans&subject=JiKen), [twitter](https://twitter.com/Ambiwlans1) #jiken, or [e-mail](mailto:udp.castellani@gmail.com). 

## Licensing/Contribute

Shoot me a message if you want to do something with this code.

## Acknowledgments

* Huge credit to [the KANJIDIC team](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project) for the initial list of kanji and definitions

## More Info

* Open alpha reddit thread: https://www.reddit.com/r/LearnJapanese/comments/eq380w/made_an_app_that_tests_your_kanji_level_in_30/
