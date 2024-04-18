#!/usr/bin/env python
import asyncio
import os
import typing
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import av
from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Accept the following environment variables from Docker
MODEL_SIZE = os.getenv('MODEL', 'base')
PROMPT = os.getenv('PROMPT', '基于FastWhisper的低延迟语音转写服务')


class ValidateFileTypeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.lower() == "post":
            try:
                logger.info(f"Request: {request.url}")
                response = await call_next(request)
                return response
            except av.error.InvalidDataError:
                return JSONResponse(status_code=400,
                                    content={"message": "Invalid file type"})
            except Exception as e:
                return JSONResponse(status_code=500,
                                    content={"message": str(e)})


app = FastAPI()
app.add_middleware(ValidateFileTypeMiddleware)


async def asyncformer(sync_func: typing.Callable, *args, **kwargs):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, sync_func, *args, **kwargs)


class Transcriber:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Transcriber, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    def __init__(
            self,
            model_size: str,
            device: str = "auto",
            compute_type: str = "default",
            prompt: str = PROMPT) -> None:
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

    async def __call__(self, audio: bytes) -> typing.AsyncGenerator[str, None]:
        def _process():
            return self._model.transcribe(BytesIO(audio),
                                          initial_prompt=self.prompt,
                                          vad_filter=True)

        segments, info = await asyncformer(_process)
        for segment in segments:
            t = segment.text
            if self.prompt in t.strip():
                continue
            if t.strip().replace('.', ''):
                logger.info(t)
                yield t


@app.post("/v1/audio/transcriptions")
async def _transcribe(file: UploadFile = File(...)):
    with Transcriber(MODEL_SIZE) as stt:
        audio = await file.read()
        text = ','.join([seg async for seg in stt(audio)])
        return {"text": text}
