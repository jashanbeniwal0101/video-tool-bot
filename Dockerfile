FROM python:3.12

WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt

RUN apt update && apt install -y ffmpeg

CMD ["python", "main.py"] 