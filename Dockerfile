FROM python:3.8-slim
WORKDIR /app/
COPY requirements.txt /app/

RUN apt update && apt install -y libpq-dev gcc portaudio19-dev
RUN pip3 install -r requirements.txt
RUN pip3 install uvicorn fastapi pydantic python-multipart loguru==0.7.0

COPY ./src/docker/whisper.py /app/

CMD ["uvicorn", "whisper:app", "--host", "0.0.0.0", "--port", "8000"]
