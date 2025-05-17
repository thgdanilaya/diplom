class URLS:
    stroi = "https://stroi.mos.ru/api/v1/block/render/organization_list?limit=10000"
    zakupki_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz223=on&fz44=on&af=on'


class Regexes:
    org_id = r'(?<=href="/organizations/).*(?=\">)'
    org_name = r'(?<=<title>).*(?=</title)'
    keywords = r"(([Ии])нформационн[а-я]{1,3}\sмоделирован[а-я]{1,3})|(BIM)|(ТИМ)|(([Тт])ехнологи[а-я]{1,3} информационного моделирования)"
    punkt_number = r"\n(\d+\.?\d?)\.?\s?(.*?\b(?:ТИМ|BIM|[И-и]{1}нформационн[а-я]{1,3} моделирован[а-я]{1,3}|[Т-т]{1}ехнологи[а-я]{1,3} информационного моделирования)\b.*?)"
    punkt_name = r"\n(\d+)\.\s(.*)\n*(\d+\.?\d?)\.?\s?(.*?\b(?:ТИМ|BIM|[И-и]{1}нформационн[а-я]{1,3} моделирован[а-я]{1,3}|[Т-т]{1}ехнологи[а-я]{1,3} информационного моделирования)\b.*?)"
    doc_names = r".*(Техническ|Тех|ТЗ).*(.(docx|DOCX)|.(pdf|PDF))"
    between_tags = r"(?<=>).*(?=<)"
    recursive_keywords = r'((?<=\d\.\s)[\s\S]*?(?:{0}))'
    find_rest = r'(?={0}).*?(?:  )'

requests = dict(
    id_request='https://stroi.mos.ru/api/v1/block/render/organization_list?limit=10000',
    name_request='https://stroi.mos.ru/organizations/'
)

delete_names = ['Департамент', 'Префектура']

messages = dict(
    no_apps='Отсутствуют заявки',
    no_customer='Отсутствует организация',
    no_keywords='Отсутствуют ключевые фразы',
    no_docs='Не найдено ТЗ',
    not_readable='Не копируемый текст ТЗ',
    is_found='Ключевые фразы присутствуют'
)
keywords = dict(
    first=r"([Ии])нформационн[а-я]{1,3}\sмоделирован[а-я]{1,3}",
    second=r'\bBIM\b',
    third=r'\bТИМ\b',
    fourth=r'([Тт])ехнологи[а-я]{1,3}\sинформационного\sмоделирования'
)
errors = dict(
    value_error='Не все переданные ключи есть в списке столбцов. Проверьте правильность заполнения словаря с данными о записи',
    org_id_error='Ошибка запроса списка ID организаций',
    org_name_error='Ошибка запроса списка организаций',
)
db = dict(
    host='DB_host',
    token='DB_token',
    elastic_token="ELASTIC_TOKEN",
    elastic_url="ELASTIC_URL",
    ACTIVE_DIRECTORY_ASSET="SERVICE_EMAIL_NOREPLY"
)
DB_columns = dict(
    ID='ID_org',
    Name='Name'
)

date_statuses = dict(
    created='Размещено',
    modified='Обновлено'
)

email_messages = dict(
    succ_subject='Отчет робота "ЕИС Закупки"',
    succ_body="Здравствуйте!\nСформирован отчет о проверке заявок на наличие ТЗ и ключевых слов.\nОбщее количество ТЗ, в которых есть ключевые слова, равно {0}\nС Уважением, Робот ДИТ\n________\nТехподдержка роботов - rpa.4me.mos.ru"
)

email = dict(
    EMAIL_SENDER="",
    bcc=[""],
    to=[]
)

report_columns = dict(
    name='Наименование заказчика',
    app_name='Наименование конкурсной процедуры',
    file_name='Наименование файла',
    is_found='Результат проверки',
    url='Ссылка на конкурс на госзакупках'
)

procurment_columns = dict(
    id='ID',
    created='DateCreate',
    modified='DateUpdate'
)

path = dict(
    download_folder='',
    data_folder='',
    report_folder='',
)