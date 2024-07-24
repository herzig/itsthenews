import re
import requests
import os
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import json
from collections import OrderedDict
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

def scrape_nzz(chrome, scroll_down=10):
    driver = chrome.get("https://www.nzz.ch")
    chrome.find_element(By.XPATH, '//*[@id="cmpwelcomebtnyes"]/a').click() # accept cookies
    WebDriverWait(driver, 2)

    html = chrome.find_element(By.TAG_NAME, 'html')
    for i in range(scroll_down):
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
    time.sleep(5)

    soup = BeautifulSoup(chrome.page_source, 'html.parser')
    img_tags = soup.find_all('img')
    return src_from_img_tags(img_tags)

def scrape_tagesanzeiger(chrome, scroll_down=10):
    chrome.get("https://www.tagesanzeiger.ch")

    html = chrome.find_element(By.TAG_NAME, 'html')
    for i in range(scroll_down):
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
    time.sleep(5)

    soup = BeautifulSoup(chrome.page_source, 'html.parser')
    img_tags = soup.find_all('img')
    
    return src_from_img_tags(img_tags)

def scrape_blick(chrome):
    chrome.get("https://www.blick.ch")
    
    soup = BeautifulSoup(chrome.page_source, 'html.parser')
    pics = soup.find_all('picture')
    meta = OrderedDict()
    for pic in pics:
        alt = pic.findChild('img').attrs['alt']
        src = pic.findChild('source').attrs['srcset'].split(' ')[0]
        filename = re.search(r'/([\w_-]+[.](webp|jpeg|jpg|gif|png)).*', src)  
        if filename is not None:
            filename = filename.group(1)
            meta[filename] = {'alt': alt, 'src': src}
    return meta

def scrape_srf(chrome):
    chrome.get("https://www.srf.ch")

    soup = BeautifulSoup(chrome.page_source, 'html.parser')
    pics = soup.find_all('picture')
    meta = OrderedDict()
    for pic in pics:
        alt = pic.findChild('img').attrs['alt']
        src = pic.findChild('source')
        if src is None:
            continue
        src = src.attrs['srcset'].split(' ')[0]
        filename = re.search(r'/([\w_-]+[.](webp|jpeg|jpg|gif|png)).*', src)  
        if filename is not None:
            filename = filename.group(1)
            meta[filename] = {'alt': alt, 'src': src}
    return meta

def scrape_20min(chrome):
    response = requests.get('https://20min.ch')
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    return src_from_img_tags(img_tags)


def src_from_img_tags(img_tags):
    meta = OrderedDict() # {}
    for img in img_tags:
        #print(img)
        if 'src' in img.attrs:
            url = img['src']
            filename = re.search(r'/([\w_-]+[.](webp|jpeg|jpg|gif|png)).*', url)
            if filename is not None:
                filename = filename.group(1)
                meta[filename] = {'alt': img.get('alt', None), 'src': url}
            if len(meta) > max_imgs:
                break
        else:
            print(f"no src in {img}")

    return meta

def download_imgs(meta: dict, out_dir: str, max_imgs=30):

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=4)

    for i, (file, dat) in enumerate(meta.items()):
        try:
            with open(os.path.join(out_dir, file), 'wb') as f:
                url = dat['src']
                if 'http' not in url:
                    url = f'{site}{url}'
                response = requests.get(url)
                f.write(response.content)
                if i == max_imgs:
                    break
        except ex:
            print(f'error downloading file {url}: ex')


sites = { 'nzz.ch': scrape_nzz, 'tagesanzeiger.ch': scrape_tagesanzeiger, 'blick.ch': scrape_blick, '20min.ch': scrape_20min, 'srf.ch': scrape_srf }
max_imgs = 30

print(f'start scrape...')
options = webdriver.ChromeOptions()
chrome = webdriver.Remote(command_executor="http://localhost:4444", options=options)
print(f'driver connected')

for site, img_tag_call in sites.items():
    print(f'site: {site}')

    meta = img_tag_call(chrome)

    new_meta = OrderedDict()
    for i, (file, dat) in enumerate(meta.items()):
        new_meta[f'{i:04d}_{file}'] = dat
        if i == max_imgs-1:
            break

    print(f'downloading {len(new_meta)} images')

    out_dir = os.path.join('scraped', site, time.strftime("%Y-%m-%d_%H-%M-%S"))
    download_imgs(new_meta, out_dir)

chrome.quit()
