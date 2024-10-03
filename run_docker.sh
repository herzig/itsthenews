#!/bin/sh

docker run --net=host --volume scraped:/scraped scraper
