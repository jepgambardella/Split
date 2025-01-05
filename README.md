# split
 Split! is a script to split videos with ffmpeg.

 Python 3.7 is required.

It's nothing new, but it simplefies the use of ffmpeg. 

Run the script with:

`python split.py`

You can choose 2 different options:

1. Split the video in chunks by entering the quantity

2. Split the video in a certain time-range. The last clip, if shorter, will be mantained.

You can choose to split it without re-encoding the video or not. 
The quickest but less precise way is without re-encoding, but if you need a precise split, you can re-encode the video in the desired format.


