# ppt2video
Generates slideshow from google presentation and audio files per slide

#### Dependencies:
FFMPEG

#### MacOS:
brew should be installed

In bash shell, run once:
brew install ffmpeg
pip install -r requirements.txt

#### Execute:
Change FILE_ID in ppt2video.py from google presentation URL
Save

Audio files must be saved in audio folder in sequence like 000.mp3, 001.mp3

#### Generate video
In bash shell, run:
python ppt2video.py
