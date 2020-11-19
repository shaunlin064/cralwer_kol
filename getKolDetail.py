#!/usr/bin/python3
import json
import os
from os import getenv

import numpy as np
import threading
from alive_progress import alive_bar
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep


def set_default(data):
    if 'kol_class' not in data:
        data['kol_class'] = {}
    if 'introduction' not in data:
        data['introduction'] = ''
    return data


def sort_file(lists):
    new_lists = []
    for item in lists:
        new_lists.append([int(s) for s in item.split('.') if s.isdigit()][0])
    new_lists.sort()
    return new_lists


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
    sleep(1)
    driver.find_element_by_name("account").send_keys(getenv('FLUENCER_ACCOUNT'))
    driver.find_element_by_css_selector("#login_password").send_keys(
            getenv("FLUENCER_PASSWORD"))
    driver.find_element_by_css_selector("#form-login").submit()
    sleep(1)
    return driver


def get_all_file_open_status():
    all_file = os.listdir(getenv('KOL_FILE_PATH'))
    open_status_file_lists = []

    escape_file_lists = ['.DS_Store']
    with alive_bar(len(all_file)) as bar:
        for file_name in all_file:
            if file_name not in escape_file_lists:
                data = load_file(file_name)

                if 'status' not in data:
                    data['status'] = 0
                    save_file(file_name, data)

                if data['status'] == 0:
                    open_status_file_lists.append(file_name)
            bar()
    return sort_file(open_status_file_lists)


def get_all_file_lists():
    return sort_file(os.listdir(getenv('KOL_FILE_PATH')))


def load_file(file_name):
    file_path = getenv('KOL_FILE_PATH') + '/' + file_name
    return json.loads(open(file_path, 'r').read())


def load_file_by_lists(driver, file_lists):
    file_list_name = file_lists
    total_file = len(file_list_name)
    with alive_bar(total_file) as bar:
        for kol_item in file_list_name:
            kol_item = str(kol_item) + '.txt'
            kol_file = load_file(kol_item)

            if kol_file['status'] == 0:
                crawl_kol_data(driver, kol_file)
            bar()
        driver.quit()


def crawl_kol_data(driver, kol_page_file):
    url = getenv('FLUENCER_KOL_PAGE') + kol_page_file['id']
    driver.get(url)

    is_loading(driver)

    message = {
        'id': kol_page_file['id'],
        'name': kol_page_file['name'],
        'crawl_finish': 'no',
        'reason': ''
        }

    check_variable = False

    try:
        kol_info_xpath = driver.find_element_by_css_selector(
                '.kol-info__info').find_elements_by_class_name('kol-info__info-field')
        check_variable = True
    except Exception as e:
        os.remove(getenv('KOL_FILE_PATH') + '/' + str(kol_page_file['id']) + '.txt')
        message['reason'] = 'not existis'
        print(message)

    # 確認是否有該kol page
    if check_variable:
        kol_page_file = set_default(kol_page_file)

        # 簡介
        kol_page_file['introduction'] = driver.find_element_by_css_selector(
                ".kol-info__introduction").text

        # 分類
        kol_page_file = set_info(kol_info_xpath, kol_page_file)

        # get social media data
        set_social_media_result = set_social_media_data(driver, kol_page_file)
        kol_page_file = set_social_media_result[1]
        # set finish
        if set_social_media_result[0]:
            kol_page_file['status'] = 1
        else:
            message['reason'] = 'set_social_media fail'
            print(message)

        save_file(kol_page_file['id']+'.txt', kol_page_file)

        message['crawl_finish'] = 'yes'


def set_info(kol_info_xpath, kol_page_file):
    for kol_info_item_xpath in kol_info_xpath:
        conten_name = kol_info_item_xpath.find_element_by_css_selector('h4').text

        if conten_name == '社群平台':
            # kol 社群平台 url
            channel_xpath = kol_info_item_xpath.find_elements_by_css_selector(
                    '.kol-info__info-content a')

            for social_media_xpath in channel_xpath:
                social_media = social_media_xpath.get_attribute('title')
                social_media_url = social_media_xpath.get_attribute('href')
                if 'social_media' not in kol_page_file:
                    kol_page_file['social_media'] = {}
                if social_media not in kol_page_file['social_media']:
                    kol_page_file['social_media'][social_media] = {}
                kol_page_file['social_media'][social_media][
                    'social_media_url'] = social_media_url

        elif conten_name == '產業分類':
            # kol 產業分類
            kol_page_file['kol_class']['industry'] = []
            data_xpath = kol_info_item_xpath.find_element_by_class_name(
                    'kol-info__info-content')
            for item in data_xpath.text.split(','):
                kol_page_file['kol_class']['industry'].append(item.strip())

        elif conten_name == '外型/形象':
            # kol 形象
            kol_page_file['kol_class']['images'] = []
            data_xpath = kol_info_item_xpath.find_element_by_class_name(
                    'kol-info__info-content')
            for item in data_xpath.text.split(','):
                kol_page_file['kol_class']['images'].append(item.strip())

        elif conten_name == '合作品項':
            # 合作品項
            # if 'match' not in kol_page_file['kol_class']:
            kol_page_file['kol_class']['match'] = []
            data_xpath = kol_info_item_xpath.find_element_by_class_name(
                    'kol-info__info-content')
            for item in data_xpath.text.split(','):
                kol_page_file['kol_class']['match'].append(item.strip())
    return kol_page_file


def set_social_media_data(driver, kol_page_file):

    for target_social_name in kol_page_file['social_media']:
        if target_social_name != 'blog':
            social_btn = find_social_btn(driver, target_social_name)

            status = False
            if social_btn is not None:

                cards = driver.find_elements_by_css_selector('.kol-info__cards .card')

                kol_page_file['social_media'][target_social_name]['data'] = []
                status = True
                for card in cards:
                    crawl_data = {
                        'title': card.find_element_by_css_selector('h4').text,
                        'name': card.find_element_by_css_selector(
                                '.data-group__data').get_attribute('id'),
                        'value': card.find_element_by_css_selector('.data-group__data').text,
                        }
                    kol_page_file['social_media'][target_social_name]['data'].append(crawl_data)


    return [status, kol_page_file]


def find_social_btn(driver, btn_name):
    wait_second = 0.1
    escape_second = 0

    can_click_select = True
    while can_click_select:
        if escape_second > 0.5:
            break
        escape_second += wait_second
        try:
            scroll_to_top(driver)
            select_buttons = driver.find_element_by_css_selector('.ss-single-selected')
            select_buttons.click()
            can_click_select = False
            sleep(wait_second)
        except Exception as e:
            sleep(wait_second)

    option_btn = driver.find_elements_by_css_selector('.ss-option')

    for item in option_btn:
        escape_second = 0
        if btn_name == item.text.lower():
            if 'ss-disabled' not in item.get_attribute('class'):
                can_click = True
                while can_click:
                    if escape_second > 0.5:
                        break
                    escape_second += wait_second
                    try:
                        scroll_to_top(driver)
                        select_buttons.click()
                        item.click()
                        can_click = False
                        is_loading(driver)
                        sleep(wait_second)
                    except Exception as e:
                        sleep(wait_second)
            return item


def scroll_to_top(driver):
    js = "var q=document.documentElement.scrollTop=0"
    driver.execute_script(js)
    sleep(0.5)


def get_kol_file(kol_id):
    filename = getenv('KOL_FILE_PATH') + '/' + kol_id + '.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if os.path.exists(filename):
        f = open(filename, "r")
        result = f.read()
        f.close
    else:
        result = ''
    return result


def save_file(file_name, kol_data):
    filename = getenv('KOL_FILE_PATH') + '/' + file_name
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:
        f.write(json.dumps(kol_data))


def is_loading(driver):
    loading = str(driver.find_element_by_css_selector("body").get_attribute(
            "class"))
    wait_second = 0.1
    escape_second = 0

    while loading != '':
        if escape_second > 5:
            break
        loading = str(driver.find_element_by_css_selector("body").get_attribute(
                "class"))
        sleep(wait_second)
        escape_second += wait_second


driver_worker_number = int(input('how many worker u need : '))
load_dotenv()
need_crawl_datas = get_all_file_open_status()
print('Total File number : ' + str(len(need_crawl_datas)))

if len(need_crawl_datas) != 0:
    if len(need_crawl_datas) < 20:
        print('Notic :: File not much switch driver_worker_number to 1')
        driver_worker_number = 1

    all_file_lists = np.array_split(need_crawl_datas, driver_worker_number)

    for chunk_file_lists in all_file_lists:
        task = threading.Thread(target=load_file_by_lists, args=(login(new_driver()), chunk_file_lists))
        task.start()

