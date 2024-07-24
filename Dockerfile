FROM python:3.12

WORKDIR /

RUN pip install selenium beautifulsoup4 requests

ADD scrape.py scrape.py

CMD [ "python", "scrape.py"]
