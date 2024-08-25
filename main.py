import os
import time
import json
import random
import requests
from tqdm import tqdm
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

BOKE_DIR = "boke_data/"
IMAGE_DIR = "boke_image/"
NUM_DRIVER = 1
START_NUM = 0
END_NUM = 100000

if not os.path.exists(BOKE_DIR):
    os.mkdir(BOKE_DIR)
if not os.path.exists(IMAGE_DIR):
    os.mkdir(IMAGE_DIR)

for i in sorted([int(JP.split(".")[0]) for JP in os.listdir(BOKE_DIR)]):
    if END_NUM < i:
        break
    if START_NUM < i:
        START_NUM = i

chrome_options = Options()
chrome_options.add_argument("--headless")

def get_boke(boke_number):

    time.sleep( random.randint(0, 3) )

    driver = webdriver.Chrome(options = chrome_options)
    driver.get(f"https://bokete.jp/odai/{boke_number}")
    full_html = driver.page_source

    if "ページが見つかりません" in full_html: return

    elif "エラーが発生しました。" in full_html:
        driver.quit()
        del driver
        time.sleep( 180 )

        driver = webdriver.Chrome(options = chrome_options)
        driver.get(f"https://bokete.jp/odai/{boke_number}")
        full_html = driver.page_source

    # ボタンが押せる限りボタンを押し続ける
    tmp = 0
    while True:
        try:
            next_button = driver.find_element(By.XPATH, "//*[@id='__next']/main/div[1]/button")
            next_button.click()

            time.sleep( 0.5 )# random.randint(5, 15) )

            full_html = driver.page_source
            row_html = html.fromstring(full_html)
            containers = row_html.xpath('//div[@id="__next"]/main/div[1]/div[*]')
            if len(containers) == tmp: break
            tmp = len(containers)

        except:
            break
    
    full_html = driver.page_source
    row_html = html.fromstring(full_html)
    # num_containers = int(row_html.xpath('//*[@id="__next"]/main/div[1]/div[1]/div[3]/div/a[1]/button/text()[2]')[0])
    image_link = "https:" + row_html.xpath('//*[@id="__next"]/main/div[1]/div[1]/a/figure/img/@src')[0]
    containers = row_html.xpath('//div[@id="__next"]/main/div[1]/div[*]')

    bokes = list()
    for i, C in enumerate( containers[1:] ):
        try:
            
            boke = C.xpath('./div/div/div/div[1]/a[2]/h1/text()')[0]
            star = C.xpath('./div/div/div/div[1]/div[3]/div[1]/a/text()')
            star = int("".join(star).replace(",", ""))
            date = C.xpath('./div/div/div/div[1]/div[3]/div[2]/a/text()')[0]

            bokes.append({
                "boke" : boke,
                "star" : star,
                "date" : date
            })
            # print(i, boke, star, date )

        except:
            continue
    # print(len(bokes), num_containers, len(containers), image_link)

    if len(bokes) == 0: return
    with open(f"{BOKE_DIR}{boke_number}.json", "w") as f:
        json.dump({
            "image_link" : image_link,
            "bokes" : bokes
        }, f)
    # print(boke_number, len(bokes))

    response = requests.get(image_link)
    if response.status_code == 200:
        with open(f"{IMAGE_DIR}{boke_number}.jpg", "wb") as f:
            f.write(response.content)

    driver.quit()

with ThreadPoolExecutor(max_workers = NUM_DRIVER) as executor:
    futures = [executor.submit(get_boke, i) for i in range(START_NUM, START_NUM + 100000)]
    for future in tqdm(futures):
        future.result()

# container
# //*[@id="__next"]/main/div[1]/div[*]
# boke
# //*[@id="__next"]/main/div[1]/div[*]/div/div/div/div[1]/a[2]/h1/text()
# star
# //*[@id="__next"]/main/div[1]/div[*]/div/div/div/div[1]/div[3]/div[1]/a/text()[2]
# date
# //*[@id="__next"]/main/div[1]/div[*]/div/div/div/div[1]/div[3]/div[2]/a/text()
