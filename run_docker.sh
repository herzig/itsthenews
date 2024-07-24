#!/bin/sh

docker run -it --net=host --volume scraped:/scraped scraper
