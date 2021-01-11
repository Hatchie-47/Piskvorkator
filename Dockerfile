FROM python:3.8
ADD gameboard.py /
ADD piskvorkator.py /
ADD dockerator.py /
ADD piskvorkator.ini /

RUN mkdir /saves

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./dockerator.py" ]