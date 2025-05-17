import docx2txt
import requests
import re
import pandas as pd
import unicodedata
from html import unescape
import os
from pypdf import PdfReader
import shutil
import config
from datetime import datetime as dt, timedelta
import numpy as np
from database import Database as db

from pathlib import Path


class Report:
    """Класс, описывающий функции работы с файлом-отчётом."""

    template_path = os.path.join(config.path['report_folder'], config.files['report_template'])
    monday = dt.now() - timedelta(days=dt.now().weekday())
    sunday = monday + timedelta(days=6)
    file_path = os.path.join(config.path['report_folder'], config.files['report']).format(monday.strftime('%d_%m_%Y'), sunday.strftime('%d_%m_%Y'))
    columns = config.report_columns
    excel_df = pd.DataFrame()
    value_error_msg = config.errors['value_error']

    def __init__(self):
        """Метод инициализации класса. Если файла нет, то копирует из шаблона."""
        if not os.path.exists(self.file_path):
            shutil.copy(self.template_path, self.file_path)

    def add_data(self, data) -> None:
        """Метод добавления данных в файл отчёт.

        Принимает словарь и проверяет, что его ключи соответствуют названиям столбцов отчёта.
        Если соответствуют, то считывает данные из файла отчёта и соединяет их данными из data. Записывает полученный DF в файл отчёт.
        :param data: Словарь с данными для записи
        :return: None
        """
        if all(name in list(self.columns.values()) for name in list(data.keys())):
            self.excel_df = pd.read_excel(self.file_path, names=self.columns.values())
            self.excel_df = pd.concat([self.excel_df, pd.DataFrame([data])])
            sheet = "Sheet1"
            options = {}
            options['strings_to_formulas'] = False
            options['strings_to_urls'] = False
            with pd.ExcelWriter(self.file_path, mode='w', engine='openpyxl', options=options) as writer:
                self.excel_df.to_excel(writer, encoding='cp1251', index=False, sheet_name=sheet)
            del self.excel_df
        else:
            raise ValueError(self.value_error_msg)

    def get_statistics(self, filepath) -> int:
        """Метод оценки успешности полученныз данных в отчёте.

        Считывает файл-отчёт и возвращает количество успешных обработок.

        :param filepath: Путь до файла-отчёта. Необходимо передавать, т.к. отчёт отсылает за прошлую неделю.
        :return: Возвращает число успешных обработок зап прошлую неделю.
        """
        report_df = pd.read_excel(filepath, names=self.columns.values())
        return len(report_df[report_df[self.columns['is_found']] == config.messages['is_found']])


report = Report()


class Data:
    """Класс для описания вспомогательных функций и функций для работы с данными."""

    def __init__(self, db):
        """Метод инициализации класса."""
        self.result_df = None
        self.null_df = None
        self.IDs = None
        self.db = db()

    def get_ids(self):
        """Метод получения списка id организаций с сайта stroi.mos.ru.

        Отправляет GET запрос к сайту и если в отчете все хорошо, то привод полученный ответ в подходящий вид и парсит его для поиска id по регулярке.
        :return: None
        """
        # Посылаем реквест на получение списка ID организаций
        r = requests.request('GET', config.requests['id_request'])
        # C помощью регекса получаем все ID.
        if r.ok:
            self.IDs = re.findall(config.regex['org_id'], unescape(unicodedata.normalize("NFKD", r.text)))
        else:
            raise Exception(config.errors['org_id_error'])

    def get_list_to_find_names(self) -> None:
        """Метод обновления данных в БД.

        Делает запрос в БД и считывает все организации. Определяет по сформированному списку self.ID организации, которые надо удалить ( они есть в БД, но нет в списке) или наоборот, которые надо добавить в базу.
        После посылает запросы в базу для добавления/удаления данных.
        После этого находит записи в БД с пустым полем название и записывает их в аттрибут класса.
        :return: None
        """
        orgs_list = pd.DataFrame.from_records(self.db.select_orgs(), columns=config.DB_columns.values())

        orgs_to_delete = list(np.setdiff1d(orgs_list[config.DB_columns['ID']], self.IDs))
        orgs_to_insert = list(np.setdiff1d(self.IDs, orgs_list[config.DB_columns['ID']]))

        self.db.delete_orgs(sorted(orgs_to_delete, key=int))
        self.db.insert_orgs(sorted(orgs_to_insert, key=int))

        self.null_df = pd.DataFrame.from_records(self.db.select_null_names())

    def find_names(self):
        """Метод поиска имён по id организации.

        Для каждого id из списка self.null_id посылает запрос на сайт stroi.mos.ru для получения полного наименования. Если в ответе всё ок, то парсим ответ.
        После получения названия записываем его в БД.

        :return: None
        """
        if not self.null_df.empty:
            for id in self.null_df[config.DB_columns['ID']]:
                try:
                    req = requests.request('GET', config.requests['name_request'] + str(id))
                    if req.ok:
                        org_name = re.findall(config.regex['org_name'], req.text)
                        org_name = str(org_name[0]).replace('No', '№').replace('»', '').replace('«', '').replace('&quot;', '')
                        if bool([ele for ele in config.delete_names if (ele in org_name)]):
                            self.db.delete_orgs([id])
                        else:
                            self.db.update_name(org_name, str(id))

                    else:
                        print(req.text)
                        raise Exception(config.errors['org_name_error'])
                except Exception as e:
                    print(e)
            self.result_df = pd.DataFrame.from_records(self.db.select_orgs())
            del self.null_df
            del self.IDs
        else:
            return None
        print()

    def prepare_data(self):
        """Общий метод для подготовки данных для обработки."""
        self.get_ids()
        self.get_list_to_find_names()
        self.find_names()
        return self.result_df

    @staticmethod
    def clear_download_folder(folder):
        """Метод очистки папки для скачиваний.

        :param folder: Путь к папке.
        :return: None
        """
        pathlist = Path(folder).glob('*')
        for item in pathlist:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    @staticmethod
    def search_keywords(file_path, data_to_add):
        """Метод поиска в файле ключевых слов.

        Считывает текст из файла (разными способами в зависимости от расширения).
        После этого с помщью регекса определяет есть ли ключевые слова в считанном тексте и записывает в файл отчёт результат с помощью словаря data с данными о заявке.

        :param file_path: Путь до файла.
        :param data_to_add: Словарь с данными для записи в файл.
        :return: None
        """
        if file_path.__contains__('docx'):
            text = docx2txt.process(file_path)
        else:
            reader = PdfReader(file_path)
            text = ""

            for page in reader.pages:
                text += page.extract_text() + "\n"

        if text.replace('\n', '') is None or text.replace('\n', '') == "":

            data_to_add[config.report_columns['is_found']] = config.messages['not_readable']
            report.add_data(data_to_add)

            print('Не копируемый текст ТЗ')
            return

        is_found_keywords = re.findall(config.regex['keywords'], text)

        if is_found_keywords:
            data_to_add[config.report_columns['is_found']] = config.messages['is_found']

        else:
            data_to_add[config.report_columns['is_found']] = config.messages['no_keywords']

            print('Ключевые слова не найдены')
            print("hehe")
        report.add_data(data_to_add)

    @staticmethod
    def process_file(file_path, data_to_add):
        """Метод для обработки файла.

        :param file_path: Путь до файла
        :param data_to_add: словарь с данными для записи в отчет
        :return: None
        """
        dir_path = config.path['download_folder']

        filename, file_extension = os.path.splitext(file_path)
        file_path = filename + str(file_extension).lower()

        Data.search_keywords(file_path, data_to_add)
        Data.clear_download_folder(dir_path)

    @staticmethod
    def download_doc(url, destination, driver):
        """Метод скачивания документа.

        Так как мы запускаем с помощью селеноида, то напрямую скачать файл мы не можем.
        Поэтому мы формируем запрос и считываем ответ в байтах и записываем в файл.

        :param url: Сформированная ссылка для запроса.
        :param destination: Путь доп папки скачиваний.
        :param driver: Драйвер для запуска скрипта.
        :return: None
        """
        headers = {"User-Agent": driver.execute_script("return navigator.userAgent")}
        response_file = requests.get(url, headers=headers).content
        if "mnt" in destination:
            with open(destination.encode('cp1251'), "wb") as file:
                file.write(response_file)
        else:
            with open(destination, "wb") as file:
                file.write(response_file)
