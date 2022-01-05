FROM python:3.9

COPY . /app/async_chatroom

WORKDIR /app/async_chatroom

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]