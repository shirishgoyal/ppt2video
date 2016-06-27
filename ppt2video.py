
import httplib2
import os
import io
import subprocess

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from apiclient.errors import HttpError
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

import httplib2shim
httplib2shim.patch()

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'PPT to Video'
FILENAME = 'test.pdf'
FFMPEG_BIN = "ffmpeg"

FILE_ID = '1Eeq9uM05ltRXlWkltAHymkz9eNrNOhpK7OxJBpa8oWo'

RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

def print_with_carriage_return(s):
    import sys
    sys.stdout.write('\r' + s)
    sys.stdout.flush()

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'ppt2video.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def export_pdf():
    credentials = get_credentials()

    print "Authorizing..."
    http = credentials.authorize(httplib2shim.Http())
    service = discovery.build('drive', 'v3', http=http)

    # files = service.files().list().execute()
    # for f in files['files']:
    #     print f['name']
    
    print "Exporting..."
    request = service.files().export_media(fileId=FILE_ID,
                                             mimeType='application/pdf')
    fh = io.FileIO(FILENAME, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    downloader.next_chunk()

def clear_folder(folder):
    import os, shutil
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
        except Exception as e:
            print e

def generate_images():
    from wand.image import Image
    from wand.color import Color

    clear_folder('images')

    total = 0
    file = open("video.txt", "w")

    with Image(filename='test.pdf', resolution=300) as img:
        img.background_color = Color("white")
        img.alpha_channel = False
        img.save(filename='images/%03d.png')
        total = len(img.sequence)

    clear_folder('videos')

    for count in range(total):
        sequence = '%03d'%count
        generate_video(sequence)
        file.write("file 'videos/%s.mp4'\n"%sequence)

    file.close()

def generate_video(sequence):
    print "Generating frames..."

    # ffmpeg -r 25 -i %02d.png -c:v libx264 -r 30 -pix_fmt yuv420p slideshow.mp4
    # ffmpeg -loop 1 -i image.jpg -i audio.wav -c:v libx264 -tune stillimage -c:a aac -strict experimental -b:a 192k -pix_fmt yuv420p -shortest out.mp4

    # check if audio exists for slide
    if os.path.exists('audio/%s.mp3'%sequence):
        command = [FFMPEG_BIN,
                   '-y',  # (optional) overwrite output file if it exists
                   '-loop', '1',
                   '-i', 'images/%s.png'%sequence,  # input comes from a 
                   '-i', 'audio/%s.mp3'%sequence,  # input comes from a folder
                   '-strict', 'experimental',
                   '-tune', 'stillimage',
                   '-c:v', 'libx264', # video encoder
                   '-c:a', 'aac', # audio format
                   '-b:a', '192k', # audio rate
                   '-pix_fmt', 'yuv420p',
                   '-shortest',  # map audio to full video length
                   'videos/%s.mp4'%sequence]
    else:
        command = [FFMPEG_BIN,
                   '-y',  # (optional) overwrite output file if it exists
                   '-loop', '1',
                   '-i', 'images/%s.png'%sequence,  # input comes from a folder
                   '-c:v', 'libx264',
                   '-t', '5', # duration
                   '-pix_fmt', 'yuv420p',
                   '-an',  # Tells FFMPEG not to expect any audio
                   'videos/%s.mp4'%sequence]

    subprocess.call(command,stdout=None,stderr=subprocess.STDOUT)

def merge_video():
    print "Generating video..."

    # ffmpeg -f concat -i mylist.txt -c copy output
    command = [FFMPEG_BIN,
                   '-f', 
                   'concat',
                   '-i', 'video.txt',
                   '-c', 'copy',
                   'video.mp4']

    subprocess.call(command,stdout=None,stderr=subprocess.STDOUT)

def main():
    export_pdf()
    generate_images()
    merge_video()

if __name__ == '__main__':
    main()
