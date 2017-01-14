import time
import wave
import audioop
import socket
import gossip
from eva.director import handle_data_from_client
from eva.util import get_pubsub
from eva import log
from eva import conf
from eva import scheduler

pyaudio_paInt16 = 8

FORMAT = pyaudio_paInt16
CHANNELS = 1
CHUNK = conf['plugins']['audio_server']['config']['chunk']
RATE = conf['plugins']['audio_server']['config']['rate']
BUFFER = conf['plugins']['audio_server']['config']['buffer']
BIND = conf['plugins']['audio_server']['config']['bind']
PORT = conf['plugins']['audio_server']['config']['port']
SLEEP_INTERVAL = conf['plugins']['audio_server']['config']['sleep_interval']
ACTIVITY_TIMEOUT = conf['plugins']['audio_server']['config']['activity_timeout']

PUBSUB = get_pubsub()

frames = []
last_activity = time.time()

@gossip.register('eva.post_boot')
def eva_post_boot():
    scheduler.add_job(audio_stream, id="eva_audio_server")
    scheduler.add_job(listen, args=(send_to_eva,), id="eva_audio_listener")

def audio_stream():
    log.info('Listening on %s:%s for audio streams from clients' %(BIND, PORT))
    global last_activity
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind((BIND, PORT))
    while True:
        # @TODO: Need to handle multiple clients pushing audio data.
        sound_data, addr = udp.recvfrom(CHUNK * 2)
        frames.append(sound_data)
        last_activity = time.time()
    udp.close()

def listen_once(callback=None, stream=None):
    """
    Can specify a pyaudio stream.
    """
    log.info('Listening for audio data...')
    global frames
    global last_activity
    frames = []
    listen_data = []
    started = False
    while True:
        if len(frames) >= BUFFER:
            started = True
            while True:
                if len(frames) > 0:
                    data = frames.pop(0)
                    if callback is not None: callback(data)
                    if stream is not None: stream.write(data, CHUNK)
                    listen_data.append(data)
                if time.time() - last_activity > ACTIVITY_TIMEOUT: break
        if started == True: break
        time.sleep(SLEEP_INTERVAL)
    log.info('Audio data retrieved')
    return listen_data

def listen(complete_callback=None, callback=None, stream=None):
    while True:
        audio_data = listen_once(callback, stream)
        if complete_callback is not None: complete_callback(audio_data)

def capture(fname):
    data = listen_once()
    save_wave(data, fname, channels=CHANNELS, rate=RATE)

def send_to_eva(audio_data):
    # Save to close out valid wave file.
    save_wave(audio_data, '/tmp/audio_server_tmp.wav')
    audio_data = open('/tmp/audio_server_tmp.wav', 'rb').read()
    ret = {'input_audio': {'audio': audio_data, 'content_type': None}}
    handle_data_from_client(PUBSUB, ret)

def save_wave(data, fname, channels=1, rate=16000):
    """
    This function will take audio frames and store them in a wave file with the
    specified channel and rate specifications.

    :param data: Audio frames, likely captured from clients by Eva's audio_server plugin.
    :type data: list
    :param fname: The path of the file to save on disk.
    :type fname: string
    :param channels: The number of channels to use when saving the wave file.
    :type channels: int
    :param rate: The frame rate to set for the wave file.
    """
    log.info('Saving audio data to %s' %fname)
    waveFile = wave.open(fname, 'wb')
    waveFile.setnchannels(channels)
    waveFile.setsampwidth(2)
    waveFile.setframerate(rate)
    waveFile.writeframes(b''.join(data))
    waveFile.close()

def downsample_audio(source, destination, in_rate=44100, out_rate=16000):
    """
    Used to downsample a wave file.

    :param source: The source wave file.
    :type source: string
    :param destination: The path to save the downsampled wave file to.
    :type destination: string
    :param in_rate: The current rate of the source wave file.
    :type in_rate: int
    :param out_rate: The target rate for the destination wave file.
    :type out_rate: int
    """
    sample_read = wave.open(source, 'r')
    sample_write = wave.open(destination, 'w')
    n_frames = sample_read.getnframes()
    data = sample_read.readframes(n_frames)
    converted = audioop.ratecv(data, 2, 1, in_rate, out_rate, None)
    sample_write.setparams((1, 2, out_rate, 0, 'NONE', 'Uncompressed'))
    sample_write.writeframes(converted[0])

if __name__ == '__main__':
    from threading import Thread
    Ts = Thread(target=audio_stream)
    Ts.setDaemon(True)
    Ts.start()
    #Ts.join()
    capture('temp.wav')
