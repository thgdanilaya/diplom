import time
import logging
from database import Database
from zakupki import Zakupki
import config
from utils import Data


def main():
    db = Database()
    zakupki = Zakupki()
    utils = Data()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    try:
        org_ids = utils.get_ids()
        if org_ids:
            db.insert_orgs(org_ids)
        else:
            logger.warning("Не удалось получить ID организаций.")

        null_rows = db.select_null_names()
        for row in null_rows:
            org_id = row[0]
            names = utils.find_names([org_id])
            if names:
                name = names[0]
                db.update_name(org_id, name)
            else:
                logger.warning(f"Не найдено имя для организации {org_id}.")

        all_orgs = db.select_orgs()
        for org_id, org_name in all_orgs:
            logger.info(f"Обрабатываем организацию: {org_id} — {org_name}")

            selected = zakupki.select_customer(org_name)
            if not selected:
                logger.warning(f"Организация '{org_name}' не найдена на сайте закупок.")
                continue
            page_index = 1
            while True:
                logger.info(f"Страница {page_index}...")
                index = 1
                while True:
                    try:
                        app_number = zakupki.get_app_number(index)
                    except Exception:
                        break
                    if not app_number:
                        break
                    if zakupki.check_app(index):
                        obj_text = zakupki.get_object() or ''
                        data = {
                            config.report_columns['org_id']: org_id,
                            config.report_columns['org_name']: selected,
                            config.report_columns['app_number']: app_number,
                            config.report_columns['object']: obj_text
                        }
                        zakupki.goto_app(index)
                        zakupki.open_docs()
                        zakupki.process_docs(data)

                        zakupki.webdriver.close()
                        zakupki.webdriver.switch_to.window(zakupki.webdriver.window_handles[0])
                    index += 1

                if zakupki.next_page():
                    page_index += 1
                    continue
                else:
                    break

            # Сброс фильтра заказчика
            zakupki.remove_customers()
    except Exception as e:
        logger.exception("Ошибка в основном процессе:")
    finally:
        zakupki.webdriver.quit()

if __name__ == '__main__':
    main()