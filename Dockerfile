FROM python:3.8
ADD gameboard.py /
ADD piskvorkator.py /
ADD piskvorkator.ini /
CMD [ "python", "./piskvorkator.py" ]