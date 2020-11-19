#!/usr/bin/python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from os import getenv
from time import sleep
from dotenv import load_dotenv
import numpy as np
import os
import json
import threading
from alive_progress import alive_bar


def save_file(kol_data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(json.dumps(kol_data))
        f.close


def new_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    # driver.maximize_window()
    return driver


def login(driver):
    driver.get(getenv('FLUENCER_LOGIN_PAGE'))

    while not driver.find_element_by_name("account").is_enabled():
        sleep(0.1)
    driver.find_element_by_name("account").send_keys(getenv('FLUENCER_ACCOUNT'))
    driver.find_element_by_css_selector("#login_password").send_keys(
            getenv("FLUENCER_PASSWORD"))
    driver.find_element_by_css_selector("#form-login").submit()

    while not driver.find_element_by_css_selector("pre").is_displayed():
        sleep(0.1)
    driver.get(getenv('FLUENCER_BRANDS_PAGE'))
    is_loading(driver)
    return driver


def get_all_social_type_page_number(social_type):
    driver = login(new_driver())
    driver.get(getenv('FLUENCER_BRANDS_PAGE'))
    is_loading(driver)

    social_type_page = {}
    with alive_bar(len(social_type)) as bar:
        for item in social_type:
            click_abled = False
            while not click_abled:
                scroll_to_top(driver)
                try:
                    driver.find_element_by_css_selector(".icon-" + item).click()
                    click_abled = True
                except Exception as e:
                    print('icon not clickable yet')

            social_type_page[item] = get_total_page_num(driver)
            bar.text('get social page number')
            bar()

    driver.quit()
    return social_type_page


def get_total_page_num(driver):
    pagination = False

    while not pagination:
        try:
            pagination = driver.find_element_by_css_selector(
                    ".pagination__pages-total").is_displayed()
        except Exception as e:
            sleep(0.1)

    return driver.find_element_by_css_selector(".pagination__pages-total").text


def get_current_page(driver):
    return driver.find_elements_by_xpath('//form[@id="SearchKolForm"]/input[@name="page"]')[
        0].get_attribute('value')


def is_loading(driver):
    loading = str(driver.find_element_by_css_selector("body").get_attribute(
            "class"))
    while loading != '':
        loading = str(driver.find_element_by_css_selector("body").get_attribute(
                "class"))


def get_work_list(driver_worker_number, social_type_page_number):
    work_list = {}
    for i in range(driver_worker_number):
        work_list[i] = {}
        for social_name in social_type_page_number:
            work_list[i][social_name] = []
    for social_name in social_type_page_number:

        tmp_work_list = np.array_split(range(int(social_type_page_number[social_name])),
                                       driver_worker_number)
        a = 0
        for item in tmp_work_list:
            work_list[a][social_name].append(item[0]+1)
            work_list[a][social_name].append(item[-1]+1)
            a += 1
    return work_list


def star_crawl(driver, work_list):
    for social_type, limit_number in work_list.items():

        icon_btn = driver.find_element_by_class_name("icon-" + social_type)

        can_click_icon = False
        while not can_click_icon:
            try:
                scroll_to_top(driver)
                icon_btn.click()
                is_loading(driver)
                can_click_icon = True
            except Exception as e:
                print('not clickable')


        set_go_to_page_number(driver, limit_number)

        total_page = limit_number[1] if int(get_total_page_num(driver)) > int(limit_number[
                                                                                  1]) else int(
            get_total_page_num(driver))

        current_page = limit_number[0]

        with alive_bar(int(total_page - limit_number[0] + 1), bar='filling',
                       spinner='waves3') as bar:

            if int(current_page) == int(total_page):

                start_get_page_data(current_page, driver, social_type)

                bar.text('social_media : ' + str(social_type))
                bar()
            else:
                while int(current_page) != int(total_page):

                    total_page = limit_number[1] if int(get_total_page_num(driver)) > int(work_list[
                                                                                              social_type][
                                                                                              1]) else int(
                        get_total_page_num(driver))
                    current_page = get_current_page(driver)

                    start_get_page_data(current_page, driver, social_type)

                    bar.text('social_media : ' + str(social_type))
                    bar()
    driver.quit()


def start_get_page_data(current_page, driver, social_type):
    kol_data = get_kol_data(driver)
    # save file
    filename = "./storage/" + social_type + "/" + social_type + "_page_" + str(
            current_page) + ".txt"
    save_file(kol_data, filename)
    # wait for loading
    driver.find_element_by_css_selector("#paginate_next_button").click()
    is_loading(driver)


def set_go_to_page_number(driver, limit_number):
    driver.find_element_by_class_name('pagination__input').send_keys(Keys.DELETE)
    sleep(0.1)
    driver.find_element_by_class_name('pagination__input').send_keys(str(limit_number[0]))
    sleep(0.1)
    driver.find_element_by_css_selector('body').click()
    sleep(0.1)
    is_loading(driver)


def get_kol_data(driver):
    kollist_items = driver.find_elements_by_xpath(
            '//*[@class="kollist__item"]/div[@class="kollist__img-outer"]')

    kol_data = []
    for kollist_item in kollist_items:
        image_url = kollist_item.find_element_by_css_selector(
                ".kollist__img").get_attribute("src")
        name = kollist_item.find_element_by_css_selector(".kollist__img").get_attribute(
                "alt")
        page_url = kollist_item.find_element_by_css_selector("a").get_attribute("href")

        trim_id = page_url.replace(getenv('FLUENCER_KOL_PAGE'), '')
        id = trim_id[0:trim_id.find('?')]
        kol_data.append({"id": id, "url": page_url, "name": name, "image_url": image_url})

    return kol_data


def scroll_to_top(driver):
    js = "var q=document.documentElement.scrollTop=0"
    driver.execute_script(js)
    sleep(0.5)


driver_worker_number = int(input('how many worker u need : '))

load_dotenv()
_social_type = ['instagram', 'youtube', 'facebook']
social_type_page_number = get_all_social_type_page_number(_social_type)
# for test now already know page number
# social_type_page_number = {'instagram': '274', 'facebook': '66', 'youtube': '21'}

_work_list = get_work_list(driver_worker_number, social_type_page_number)

for k, chunk_file_lists in _work_list.items():
    task = threading.Thread(target=star_crawl, args=(login(new_driver()), chunk_file_lists))
    task.start()
