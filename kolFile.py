#!/usr/bin/python3
import json
import os
from os import getenv

from alive_progress import alive_bar
from dotenv import load_dotenv


class kolFile:
    def __init__(self):
        pass
    def get_all_file_open_status(self):
        all_file = os.listdir(getenv('KOL_FILE_PATH'))
        open_status_file_lists = []
        with alive_bar(len(all_file)) as bar:
            for file_name in all_file:

                data = json.loads(self.get_kol_file(file_name))

                if data['status'] == 0:
                    open_status_file_lists.append(file_name)
                bar()
        return open_status_file_lists

    def set_all_file_open_update_status(self):
        all_file = os.listdir(getenv('KOL_FILE_PATH'))
        with alive_bar(len(all_file)) as bar:
            for file_name in all_file:
                data = json.loads(self.get_kol_file(file_name))
                data['status'] = 0
                self.save_file(file_name, data)
                bar()

    def get_kol_file(self,file_name):
        filename = getenv('KOL_FILE_PATH') + '/' + file_name
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if os.path.exists(filename):
            f = open(filename, "r")
            result = f.read()
            f.close
        else:
            result = ''
        return result

    def save_file(self, file_name, kol_data):
        filename = getenv('KOL_FILE_PATH') + '/' + file_name
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w+") as f:
            f.write(json.dumps(kol_data))


load_dotenv()
t = kolFile()
print(len(t.get_all_file_open_status()))
