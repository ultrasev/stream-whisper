

```bash
git clone https://github.com/ultrasev/stream-whisper
apt -y install libcublas11 portaudio19-dev
cd stream-whisper
pip3 install -r requirements.txt
```

注：
- `libcublas11` 是 NVIDIA CUDA Toolkit 的依赖，如果需要使用 CUDA Toolkit，需要安装。
- `portaudio19-dev` 是 pyaudio 的依赖，如果系统已安装，可以忽略。


把 `.env` 文件中的 `REDIS_URL` 改成自己的 Redis 地址，然后运行 `python3 -m src.server`，服务端就启动了。

```bash
python3 -m src.server
```

然后运行 `python3 -m src.client`，客户端就启动了。运行前先测试一下麦克风是否正常工作，确认能够正常录音。 

```bash
python3 -m src.client
```


# Q&A
## Redis 地址怎么搞？
1. 自己有服务器的话， 使用 docker 可以很方便的创建一个；
2. 或者通过 [redislabs](https://app.redislabs.com/#/) 注册账号，创建免费实例，获取连接信息。免费实例有 30M 内存，足够使用。建议选择日本 AWS 区域，延迟低。

## 为什么要用 Redis？
Redis 不是必须的，从 client 端往 server 端传输数据，有很多种方法，可以根据自己的需求选择。

