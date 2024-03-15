#!/usr/bin/env python
"""
在本地进行录音 + 转写的单脚本代码。不依赖于云服务（e.g., redis, socket），适合于离线使用。

依赖安装:
    pip3 install pyaudio webrtcvad faster-whisper

运行方式:
    python3 local_deploy.py
"""
from faster_whisper import WhisperModel
from io import BytesIO
import typing
import io
import collections
import wave
import time

import pyaudio
import webrtcvad
import logging
from funasr import AutoModel  #添加标点的模型

#解决bug问题
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import openai

openai.api_key="sk-********"  #填写你自己的key

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s')

#实现标点符号的添加
model1 = AutoModel(model="E:\ct-punc")
class Transcriber(object):
    def __init__(self,
                 model_size: str = r"E:\whisper\faster-whisper-large-v3",
                 device: str = "auto",
                 compute_type: str = "default",
                 prompt: str = '实时/低延迟语音转写服务'
                 ) -> None:
        """ FasterWhisper 语音转写

        Args:
            model_size (str): 模型大小，可选项为 "tiny", "base", "small", "medium", "large" 。
                更多信息参考：https://github.com/openai/whisper
            device (str, optional): 模型运行设备。
            compute_type (str, optional): 计算类型。默认为"default"。
            prompt (str, optional): 初始提示。如果需要转写简体中文，可以使用简体中文提示。
        """

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
                                               initial_prompt=self.prompt)
        if info.language != "zh":
            return {"error": "transcribe Chinese only"}
        res_all = ""
        for segment in segments:
            t = segment.text

            res1 = model1.generate(input=t)
            res_all = res_all + res1[0]["text"]
        if res_all.strip().replace('.', ''):
            yield res_all



class AudioRecorder(object):
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

    def __iter__(self):
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
                    yield bytes(self)


def main():
    try:
        with AudioRecorder(channels=1, sample_rate=16000) as recorder:
            # print("recorder")
            with Transcriber(model_size=r"E:\whisper\faster-whisper-large-v3") as transcriber:  #选择本地的large-v3
                # print("transcriber")
                for audio in recorder:
                    # print("audio")
                    for seg in transcriber(audio):
                        # print(seg)
                        print("问：", seg)
                        # time.sleep(0.5)
                        messages = []
                        system_message = "资深工作人员"
                        system_message_dict = {
                            "role": "system",
                            "content": system_message
                        }
                        messages.append(system_message_dict)
                        user_message_dict = {
                            "role": "user",
                            "content": seg
                        }
                        messages.append(user_message_dict)
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=messages
                            )
                            # print(response)
                            reply = response["choices"][0]["message"]["content"]
                            print("++++++++++++++++++++++++++正在加速寻找答案！++++++++++++++++++++++++++")
                            time.sleep(1)
                            print("GPT答：", reply)
                        except:
                            time.sleep(1)
                            print("**************************请不要密集提问！**************************")
                        # time.sleep(0.5)
                        logging.info(seg)
                        print("--------------------------------请继续询问！--------------------------------")

    except KeyboardInterrupt:
        print("KeyboardInterrupt: terminating...")
    except Exception as e:
        logging.error(e, exc_info=True, stack_info=True)


if __name__ == "__main__":
    main()
