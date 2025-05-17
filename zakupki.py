import re
import os
import config
from datetime import datetime as dt
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import Report, Data
from database import Database as db



class Zakupki:
    class XPATH:
        CANCEL_BUTTON = r"//div[@id='modal-region']//button//span[contains(.,'Отмена')]"
        REMOVE_CUSTOMER = r"//div[contains(@id,'customerTag')]//ul/li/span"
        NEXT_PAGE = r"//ul[contains(@class,'pages')]/a"
        SELECT_CUSTOMER = r"//div[contains(text(),'Наименование заказчика')]//following-sibling::a"
        CUSTOMER_NAME_TEXTAREA = r"//div[@id='modal-customer']//input[@id='customerInputDialog']"
        CUSTOMER_SEARCH_RESULTS = r"//div[contains(@id,'mCSB')]//input//following-sibling::label"
        ENTER_CUSTOMER = r"//button[contains(text(),'ВЫБРАТЬ')]"
        SEARCH_BUTTON = r"//button/span[contains(text(),'Применить')]"
        SEARCH_COUNT = r"//div/span[text()='Результаты поиска']/parent::div/following-sibling::div"
        GO_TO_APPLICATION = r"//div[@class='search-registry-entrys-block']/div[{0}]//a[contains(text(),'№')]"
        DOCS_BUTTON = r"//div/a[contains(text(),'Документы')]"
        DOCS_MORE = r".//div//a[contains(text(),'больше')]"
        ALL_DOCS = r"//div[contains(text(),'Прикрепленные файлы')]//following-sibling::div[contains(@class,'attachment')]//span/a[last()]"
        GET_OBJECT = r"//*[contains(text(),'Объект закупки')]//following-sibling::*"
        APP_DATES = r"//div[@class='search-registry-entrys-block']/div[{0}]//div[contains(text(),'{1}')]//following-sibling::div"
        CLOSE_BUTTON = r'//*[@id="sslCertificateChecker-right"]/span'

    def __init__(self):
        options = Options()
        options.add_argument("--start-maximized")
        self.db = db()
        self.webdriver = selenium.webdriver.Chrome(options=options)
        self.webdriver.get(config.URLS.zakupki_url)
        button = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH.CLOSE_BUTTON))
        )
        button.click()

    def close_modal(self):
        """Закрыть модальное окно, если оно присутствует."""
        wait = WebDriverWait(self.webdriver, 5)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATH.CANCEL_BUTTON)))
            btn.click()
        except TimeoutException:
            pass

    def remove_customers(self):
        """Удалить всех выбранных заказчиков из фильтра."""
        wait = WebDriverWait(self.webdriver, 5)
        try:
            elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, self.XPATH.REMOVE_CUSTOMER)))
        except TimeoutException:
            return
        for el in elements:
            el.click()
            time.sleep(1)

    def next_page(self):
        """Перейти на следующую страницу результатов, если кнопка доступна."""
        wait = WebDriverWait(self.webdriver, 5)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATH.NEXT_PAGE)))
            btn.click()
            time.sleep(3)
        except TimeoutException:
            pass

    def get_object(self):
        """Получить текст поля 'Объект закупки'."""
        wait = WebDriverWait(self.webdriver, 5)
        try:
            el = wait.until(EC.visibility_of_element_located((By.XPATH, self.XPATH.GET_OBJECT)))
            return el.text.strip()
        except TimeoutException:
            return None

    def goto_app(self, index: int) -> str:
        """Открыть заявку по её порядковому номеру в списке и переключиться на новую вкладку."""
        wait = WebDriverWait(self.webdriver, 5)
        el = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATH.GO_TO_APPLICATION.format(index))))
        url = el.get_attribute('href')
        # Открываем в новой вкладке
        self.webdriver.execute_script("window.open(arguments[0], '_blank');", url)
        time.sleep(1)
        self.webdriver.switch_to.window(self.webdriver.window_handles[-1])
        return url

    def get_app_number(self, index: int) -> str | None:
        """Получить номер заявки из текста ссылки по индексу."""
        wait = WebDriverWait(self.webdriver, 5)
        try:
            el = wait.until(EC.visibility_of_element_located((By.XPATH, self.XPATH.GO_TO_APPLICATION.format(index))))
            nums = re.findall(r'\d+', el.text)
            return nums[0] if nums else None
        except TimeoutException:
            return None

    def get_app_dates(self, index: int) -> tuple[dt, dt] | None:
        """Получить даты создания и изменения заявки."""
        wait = WebDriverWait(self.webdriver, 5)
        created_xpath = self.XPATH.APP_DATES.format(index, config.date_statuses['created'])
        modified_xpath = self.XPATH.APP_DATES.format(index, config.date_statuses['modified'])
        try:
            el_created = wait.until(EC.visibility_of_element_located((By.XPATH, created_xpath)))
            el_modified = wait.until(EC.visibility_of_element_located((By.XPATH, modified_xpath)))
            date_created = dt.strptime(el_created.text.strip(), '%d.%m.%Y')
            date_modified = dt.strptime(el_modified.text.strip(), '%d.%m.%Y')
            return date_created, date_modified
        except TimeoutException:
            return None

    def check_app(self, index: int) -> bool:
        """Проверить, нужно ли обрабатывать заявку (новая или изменённая)."""
        app_number = self.get_app_number(index)
        dates = self.get_app_dates(index)
        if not app_number or not dates:
            return False
        date_created, date_modified = dates
        record = self.db.select_app(app_number)
        if not record:
            self.db.insert_app(app_number, date_created.strftime('%Y%m%d'), date_modified.strftime('%Y%m%d'))
            return True
        modified_str = date_modified.strftime('%Y-%m-%d')
        if modified_str != record[config.procurment_columns['modified']]:
            self.db.update_app_date(app_number, date_modified.strftime('%Y%m%d'))
            return True
        return False

    def open_docs(self):
        """Нажать на кнопку 'Документы' и открыть страницу документов заявки."""
        wait = WebDriverWait(self.webdriver, 10)
        el = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATH.DOCS_BUTTON)))
        href = el.get_attribute('href')
        self.webdriver.get(href)
        time.sleep(1)

    def process_docs(self, data: dict) -> None:
        """Обработать прикреплённые файлы заявки: скачать и распарсить нужные документы."""
        wait = WebDriverWait(self.webdriver, 5)
        # Раскрыть все документы, если есть кнопка 'больше'
        try:
            more = wait.until(EC.element_to_be_clickable((By.XPATH, self.XPATH.DOCS_MORE)))
            more.click()
        except TimeoutException:
            pass
        docs = self.webdriver.find_elements(By.XPATH, self.XPATH.ALL_DOCS)
        if not docs:
            data[config.report_columns['file_name']] = config.messages['no_docs']
            self.report.add_data(data)
            return
        seen = set()
        for doc in docs:
            text = doc.text or doc.get_attribute('textContent')
            if re.search(r".*(Техническ|Тех|ТЗ).*", text, re.IGNORECASE):
                href = doc.get_attribute('href')
                name = os.path.basename(href)
                ext = os.path.splitext(name)[1].lower()
                if ext in ('.pdf', '.docx') and name not in seen:
                    seen.add(name)
                    data[config.report_columns['file_name']] = name
                    file_path = os.path.join(self.file_path, f'Downloaded_doc{ext}')
                    Data.download_doc(driver=self.webdriver, url=href, destination=file_path)
                    # Ожидание завершения скачивания
                    timeout = 10
                    elapsed = 0
                    while not os.path.exists(file_path) and elapsed < timeout:
                        time.sleep(1)
                        elapsed += 1
                    Data.process_file(file_path, data)
                    self.report.add_data(data)

    def select_customer(self, customer):
        wait = WebDriverWait(self.webdriver, 10)
        select_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH.SELECT_CUSTOMER))
        )
        select_btn.click()
        textarea = wait.until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH.CUSTOMER_NAME_TEXTAREA))
        )
        textarea.clear()
        n = 20
        chunks = [customer[i:i+n] for i in range(0, len(customer), n)]
        accumulated = ""
        for chunk in chunks:
            textarea.send_keys(chunk)
            accumulated += chunk
            try:
                wait_short = WebDriverWait(self.webdriver, 2)
                wait_short.until(lambda d: textarea.get_attribute("value").startswith(accumulated))
            except TimeoutException:
                textarea.send_keys(chunk)
                wait_short.until(lambda d: textarea.get_attribute("value").startswith(accumulated))
        try:
            result = wait.until(
                EC.visibility_of_element_located((By.XPATH, self.XPATH.CUSTOMER_SEARCH_RESULTS))
            )
        except TimeoutException:
            return False
        name_full = result.text.strip()
        result.click()
        enter_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH.ENTER_CUSTOMER))
        )
        enter_btn.click()
        search_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH.SEARCH_BUTTON))
        )
        search_btn.click()

        return name_full
