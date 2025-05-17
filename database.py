import psycopg2
from psycopg2 import sql
import config
import queries

class Database:
    """
    Слой работы с базой данных.
    Обёртка над psycopg2 для простых CRUD операций.
    """
    def __init__(self, dsn: str = None):
        """
        :param dsn: Строка подключения к базе (DSN). Если не передан, используется config.Settings.db_dsn
        """
        self.dsn = dsn
        self.conn = psycopg2.connect(self.dsn)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()

    def _execute_select_all(self, query: str):
        """Выполнить SELECT и вернуть все строки."""
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
        except Exception:
            self.conn.rollback()
            raise

    def _execute_select_one(self, query: str):
        """Выполнить SELECT и вернуть первую строку."""
        try:
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            return row
        except Exception:
            self.conn.rollback()
            raise

    def _execute_insert(self, query: str):
        """Выполнить INSERT и зафиксировать изменения."""
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _execute_update(self, query: str):
        """Выполнить UPDATE/DELETE и зафиксировать изменения."""
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def select_orgs(self):
        """Вернуть все записи из таблицы Procurement_Organization."""
        return self._execute_select_all(queries.select_all_orgs)

    def update_name(self, id: int, org_name: str):
        """Обновить имя организации по id."""
        q = queries.update_name.format(id, org_name)
        return self._execute_update(q)

    def select_null_names(self):
        """Вернуть организации без имени (Name IS NULL)."""
        return self._execute_select_all(queries.select_null_names)

    def insert_orgs(self, ids: list[int]):
        """Вставить список id организаций."""
        if not ids:
            return
        # Формируем VALUES
        vals = ",".join(f"({i})" for i in ids)
        q = queries.insert_orgs.format(vals)
        return self._execute_insert(q)

    def delete_orgs(self, ids: list[int]):
        """Удалить организации по списку id."""
        if not ids:
            return
        vals = ",".join(str(i) for i in ids)
        q = queries.delete_orgs.format(f"({vals})")
        return self._execute_update(q)

    def select_app(self, app_id: str):
        """Вернуть запись заявки по её app_id."""
        q = queries.select_app_id.format(app_id)
        return self._execute_select_one(q)

    def insert_app(self, app_id: str, date_created: str, date_modified: str):
        """Вставить новую заявку с датами."""
        q = queries.insert_app.format(app_id, date_created, date_modified)
        return self._execute_insert(q)

    def update_app_date(self, app_id: str, date_modified: str):
        """Обновить дату изменения заявки."""
        q = queries.update_app_mod_date.format(date_modified, app_id)
        return self._execute_update(q)
