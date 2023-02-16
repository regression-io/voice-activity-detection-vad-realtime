import asyncio
import websockets
import webrtcvad
import sys


vad = webrtcvad.Vad(3)

class AudioStream:
    def __init__(self) -> None:
        self.sample_rate = 16000
        self.frame_size = 320
        self.bytes_per_sample = 2
        self.idle_cut = (self.sample_rate/2)/self.frame_size # chunk audio if no voice for 0.5 seconds
        self.last_voice_activity = 0

    def convert_buffer_size(self, audio_frame):
        while len(audio_frame) < (self.frame_size * self.bytes_per_sample):
            audio_frame = audio_frame + b'\x00'
        return audio_frame
    
    def voice_activity_detection(self, audio_frame):
        converted_frame = self.convert_buffer_size(audio_frame)
        is_speech = vad.is_speech(converted_frame, sample_rate=self.sample_rate)
        if is_speech:
            self.last_voice_activity = 0
            return "1"
        else:
            if self.last_voice_activity == self.idle_cut:
                self.last_voice_activity = 0
                return "X"
            else:
                self.last_voice_activity += 1
                return "_"

audiostream = AudioStream()
async def handler(websocket, path):
    print(f"WebSocket connection established for client from {path}")
    try:
        async for message in websocket:
            is_active = audiostream.voice_activity_detection(message)
            sys.stdout.write(is_active)
            sys.stdout.flush()
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket connection closed for client")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        await websocket.close()

async def main():
    PORT = 5000
    async with websockets.serve(handler, 'localhost', PORT):
        print(f"WebSocket server started at ws://localhost:{PORT}")
        await asyncio.Future()

asyncio.run(main())