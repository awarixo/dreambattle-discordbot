FROM python:3.8

RUN mkdir /standard-bot && chmod 777 /standard-bot 

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3","main.py"]