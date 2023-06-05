from yt_dlp import YoutubeDL

ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
        'preferredquality': '128',
    }],
    "outtmpl": "audio.m4a"
}

with YoutubeDL(ydl_opts) as ydl:
    ydl.download(["https://www.youtube.com/watch?v=4XFaO2CLELY"])
