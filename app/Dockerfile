FROM python
WORKDIR /CraftersHelper
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY src /CraftersHelper/src

CMD [ "python3", "./src/app.py" , "--host=0.0.0.0:8050"]