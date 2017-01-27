Audio Server
============

An Eva plugin that allows the handling of real-time streamed audio data from clients.

## Installation

Can be easily installed through the Web UI by using [Web UI Plugins](https://github.com/edouardpoitras/eva-web-ui-plugins).

Alternatively, add `audio_server` to your `eva.conf` file under the `enabled_plugins` option and restart Eva.

## Usage

Once installed, clients will be able to stream raw audio data directly to Eva through the UDP port configured (default is 8800).

#### Audio Stream

Audio Server expects a stream of single-channel raw audio frames that have been captured with something like PyAudio.

#### Handling Data

Once audio data from a client has been received, it is saved to disk as a wave file and sent through Eva's standard interaction process.

The resulting response from Eva will be handled as any other interaction and arrive at the client assuming they are listening to the proper pubsub channel for Eva responses.

As of version 0.1.0, Audio data should NOT be continuously streamed without interruption (being addressed in [issue #1](https://github.com/edouardpoitras/eva-audio-server/issues/1)).
The client should be smart enough (voice activity detector and/or activation keyword) to only send over audio data when a query/request from the user is under way.
Otherwise `audio_server` will not know when to terminate a query/question and send it for processing.

## Configuration

Default configurations can be chanaged by adding a `audio_server.conf` file in your plugin configuration path (can be configured in `eva.conf`, but usually `~/eva/configs`).

To get an idea of what configuration options are available, you can take a look at the `audio_server.conf.spec` file in this repository, or use the [Web UI](https://github.com/edouardpoitras/eva-web-ui) plugin and view them at `/plugins/configuration/audio_server`.

Here is a breakdown of the available options:

    chunk
        Type: Integer
        Default: 1024
        The batche size for audio data being received from clients via UDP.
    rate
        Type: Integer
        Default: 16000
        The audio sample rate to use when saving the audio data to disk.
    buffer
        Type: Integer
        Default: 5
        The number of frames to receive before beginning to process the audio data from the client.
        Higher value means smoother streaming, but more delay before processing begins.
    port
        Type: Integer
        Default: 8800
        The UDP port that audio_server will listen on for audio data from clients.
    bind
        Type: String
        Default: '0.0.0.0'
        The address for audio_server to listen on ('0.0.0.0' means any).
    sleep_interval
        Type: Float
        Default: 0.1
        A performance metric.
        The number of seconds to pause between loop iterations before checking if audio data is coming in from clients.
    activity_timeout
        Type: Float
        Default: 1.0
        The number of seconds to wait after receiving audio data before packaging it up and sending it to Eva as a single complete query/command.
        If the client is already taking care of terminating the audio stream once there is no more voice activity, then this value can be reduced from it's default of 1.0 to increase responsiveness from Eva.
        However, with a value nearing 0, audio_server may mistake a single query/command for multiple rapid query/commands as network packets stream in.
