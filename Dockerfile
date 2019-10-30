FROM python:3

WORKDIR /home/python-folder

RUN pip install beautifulsoup4 requests

CMD ["python", "api_parser.py"]
