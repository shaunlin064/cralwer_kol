#!/usr/bin/python3
import json
import os

import datetime
from alive_progress import alive_bar


class trimKolRowFile:
    def __init__(self):
        self.kol_data_path = 'kol'
        self.file_path = 'storage'
        self.social_medias = os.listdir(self.file_path)

    def load_file(self):
        today = datetime.date.today()
        created_at_mark  = today - datetime.timedelta(days=today.weekday())
        created_at_mark  = created_at_mark.strftime("%Y/%m/%d 00:00:00")
        for social_media in self.social_medias:
            file_path = self.file_path + '/' + social_media
            files = os.listdir(file_path)
            with alive_bar(len(files)) as bar:
                for file in files:

                    kol_page_file = json.loads(open(file_path + '/' + file, 'r').read())
                    for kol_item in kol_page_file:
                        kol_data = self.get_kol_file(kol_item['id'])

                        if not len(kol_data):
                            kol_data = {}
                        else:
                            kol_data = json.loads(kol_data)

                        # set default Data
                        kol_data['id'] = kol_item['id']

                        if 'social_media' not in kol_data:
                            kol_data['social_media'] = {}

                        if social_media not in kol_data['social_media']:
                            kol_data['social_media'][social_media] = {}

                        kol_data['name'] = kol_item['name']
                        kol_data['social_media'][social_media]['name'] = kol_item['name']
                        kol_data['social_media'][social_media]['image_url'] = kol_item['image_url']
                        kol_data['created_at'] = created_at_mark

                        if 'status' not in kol_data:
                            kol_data['status'] = 0

                        # save file
                        self.save_file(kol_data['id'], kol_data)
                    bar()

    def get_kol_file(self, id):
        filename = self.kol_data_path + '/' + id + '.txt'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if os.path.exists(filename):
            with open(filename, "r") as f:
                result = f.read()
        else:
            result = ''
        return result

    def save_file(self, id, kol_data):
        filename = self.kol_data_path + '/' + id + '.txt'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w+") as f:
            f.write(json.dumps(kol_data))


trimKolRowFile = trimKolRowFile()
trimKolRowFile.load_file()
