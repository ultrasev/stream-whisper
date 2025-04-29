#!/usr/bin/env python
"""
在本地进行录音 + 转写的单脚本代码。不依赖于云服务（e.g., redis, socket），适合于离线使用。

依赖安装:
    pip3 install pyaudio webrtcvad faster-whisper

运行方式:
    python3 local_deploy.py
"""

import collections
import io
import logging
import queue
import threading
import typing
import wave
from io import BytesIO

import pyaudio
import webrtcvad
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO,
                    format='%(name)s - %(levelname)s - %(message)s')


class Queues:
    audio = queue.Queue()
    text = queue.Queue()


class Transcriber(threading.Thread):
    def __init__(
            self,
            model_size: str,
            device: str = "auto",
            compute_type: str = "default",
            prompt: str = '实时/低延迟语音转写服务，林黛玉、倒拔、杨柳树、鲁迅、周树人、关键词、转写正确') -> None:
        """ FasterWhisper 语音转写

        Args:
            model_size (str): 模型大小，可选项为 "tiny", "base", "small", "medium", "large" 。
                更多信息参考：https://github.com/openai/whisper
            device (str, optional): 模型运行设备。
            compute_type (str, optional): 计算类型。默认为"default"。
            prompt (str, optional): 初始提示。如果需要转写简体中文，可以使用简体中文提示。
        """
        super().__init__()
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.prompt = prompt

    def __enter__(self) -> 'Transcriber':
        self._model = WhisperModel(self.model_size,
                                   device=self.device,
                                   compute_type=self.compute_type)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def __call__(self, audio: bytes) -> typing.Generator[str, None, None]:
        segments, info = self._model.transcribe(BytesIO(audio),
                                                initial_prompt=self.prompt,
                                                vad_filter=True)
        # if info.language != "zh":
        #     return {"error": "transcribe Chinese only"}
        for segment in segments:
            t = segment.text
            if self.prompt in t.strip():
                continue
            if t.strip().replace('.', ''):
                yield t

    def run(self):
        while True:
            audio = Queues.audio.get()
            text = ''
            for seg in self(audio):
                logging.info(seg)
                text += seg
            Queues.text.put(text)


class AudioRecorder(threading.Thread):
    """ Audio recorder.
    Args:
        channels (int, 可选): 通道数，默认为1（单声道）。
        rate (int, 可选): 采样率，默认为16000 Hz。
        chunk (int, 可选): 缓冲区中的帧数，默认为256。
        frame_duration (int, 可选): 每帧的持续时间（单位：毫秒），默认为30。
    """

    def __init__(self,
                 channels: int = 1,
                 sample_rate: int = 16000,
                 chunk: int = 256,
                 frame_duration: int = 30) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.frame_size = (sample_rate * frame_duration // 1000)
        self.__frames: typing.List[bytes] = []

    def __enter__(self) -> 'AudioRecorder':
        self.vad = webrtcvad.Vad()
        # 设置 VAD 的敏感度。参数是一个 0 到 3 之间的整数。0 表示对非语音最不敏感，3 最敏感。
        self.vad.set_mode(1)

        self.audio = pyaudio.PyAudio()
        self.sample_width = self.audio.get_sample_size(pyaudio.paInt16)
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def __bytes__(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.__frames))
            self.__frames.clear()
        return buf.getvalue()

    def run(self):
        """ Record audio until silence is detected.
        """
        MAXLEN = 30
        watcher = collections.deque(maxlen=MAXLEN)
        triggered, ratio = False, 0.5
        while True:
            frame = self.stream.read(self.frame_size)
            is_speech = self.vad.is_speech(frame, self.sample_rate)
            watcher.append(is_speech)
            self.__frames.append(frame)
            if not triggered:
                num_voiced = len([x for x in watcher if x])
                if num_voiced > ratio * watcher.maxlen:
                    logging.info("start recording...")
                    triggered = True
                    watcher.clear()
                    self.__frames = self.__frames[-MAXLEN:]
            else:
                num_unvoiced = len([x for x in watcher if not x])
                if num_unvoiced > ratio * watcher.maxlen:
                    logging.info("stop recording...")
                    triggered = False
                    Queues.audio.put(bytes(self))
                    logging.info("audio task number: {}".format(
                        Queues.audio.qsize()))


class Chat(threading.Thread):
    def __init__(self, prompt: str) -> None:
        super().__init__()
        self.prompt = prompt

    def run(self):
        prompt = "Hey! I'm currently working on my English speaking skills and I was hoping you could help me out. If you notice any mistakes in my expressions or if something I say doesn't sound quite right, could you please correct me? And if everything's fine, just carry on with a normal conversation. I'd really appreciate it if you could reply in a conversational, spoken English style. This way, it feels more like a natural chat. Thanks a lot for your help!"
        while True:
            text = Queues.text.get()
            if text:
                import os
                os.system('chat "{}"'.format(prompt + text))
                prompt = ""


def main():
    try:
        with AudioRecorder(channels=1, sample_rate=16000) as recorder:
            with Transcriber(model_size="base") as transcriber:
                recorder.start()
                transcriber.start()
                # chat = Chat("")
                # chat.start()

                recorder.join()
                transcriber.join()

    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        logging.error(e, exc_info=True, stack_info=True)


if __name__ == "__main__":
    main()
