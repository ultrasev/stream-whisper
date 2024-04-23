# 使用 Faster-whisper 模拟实时语音转写

<figure style="text-align: center; radius:10pt">
    <img src="assets/flow.gif" width=689pt radius=10pt>
</figure>
<div align="center">

<a href='https://follow-your-click.github.io/'><img src='https://img.shields.io/badge/Project-Page-Green'></a> ![visitors](https://visitor-badge.laobi.icu/badge?page_id=ultrasev.stream-whisper&left_color=green&right_color=red)  [![GitHub](https://img.shields.io/github/stars/ultrasev/stream-whisper?style=social)](https://github.com/ultrasev/stream-whisper)
</div>


# 使用方法
## 1. 拆分服务端与客户端
适合 GPU 在云端的场景。
### 服务端
负责接收客户端发送的音频数据，进行语音识别，然后把识别结果返回给客户端。
```bash
git clone https://github.com/ultrasev/stream-whisper
apt -y install libcublas11
cd stream-whisper
pip3 install -r requirements.txt
```

注：
- `libcublas11` 是 NVIDIA CUDA Toolkit 的依赖，如果需要使用 CUDA Toolkit，需要安装。
- 经 [@muzian666](https://github.com/muzian666) 提示，aioredis 包目前仍然不支持 Python3.11，Python 版本建议 3.8 ~ 3.10

把 `.env` 文件中的 `REDIS_SERVER` 改成自己的 Redis 地址，然后运行 `python3 -m src.server`，服务端就启动了。
第一次执行时，会从 huggingface 上下载语音识别模型，需要等待一段时间。Huggingface 已经被防火墙特别对待了，下载速度很慢，建议使用代理。


### 客户端
负责录音，然后把音频数据发送给服务端，接收服务端返回的识别结果。

```bash
git clone https://github.com/ultrasev/stream-whisper
apt -y install portaudio19-dev
cd stream-whisper
pip3 install -r requirements.txt
```

注：
- `portaudio19-dev` 是 pyaudio 的依赖，如果系统已安装，可以忽略。

同样需要把 `.env` 文件中的 `REDIS_SERVER` 改成自己的 Redis 地址，在本地机器上运行 `python3 -m src.client`，客户端就启动了。运行前先测试一下麦克风是否正常工作，确认能够正常录音。

## 2. 本地直接运行
如果本地有 GPU，可以直接运行 `src/local_deploy.py`，这样就可以在本地直接运行服务端和客户端了。
```bash
git clone https://github.com/ultrasev/stream-whisper
apt -y install portaudio19-dev  libcublas11
python3 src/local_deploy.py
```


# Docker 一键部署自己的 whisper 转写服务
```bash
docker run -d --name whisper -p 8000:8000 ghcr.io/ultrasev/whisper
```
接口兼容 OpenAI 的 [API 规范](https://platform.openai.com/docs/guides/speech-to-text)，可以直接使用 OpenAI 的 SDK 进行调用。

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000")

audio_file= open("/path/to/file/audio.mp3", "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1",
  file=audio_file
)
print(transcription.text)
```


# 可优化方向
1. 缩短静音间隔，提高实时性。默认静音间隔是 0.5 秒，可以根据自己的需求在 `client.py` 中调整。
2. 使用更好的语音识别模型，提高识别准确率。

# Q&A
## Redis 地址怎么搞？
1. 自己有带有公网 IP 的服务器的话， 使用 docker 可以很方便的创建一个；
2. 或者通过 [redislabs](https://app.redislabs.com/#/) 注册账号，创建一个免费实例，获取连接信息。免费实例有 30M 内存，足够使用。建议选择日本 AWS 区域，延迟低。

## 为什么要用 Redis？
Redis 不是必须的，从 client 端往 server 端传输数据，有很多种方法，可以根据自己的需求选择。
