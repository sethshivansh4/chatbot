FROM python:3.9

WORKDIR /backend

ADD main.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 9000

CMD ["python", "main.py"]

