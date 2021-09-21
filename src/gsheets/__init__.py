import gspread

from utils.config import sheet_id

google_client = gspread.service_account(filename=r"./utils/credentials_google.json")
spreadsheet = google_client.open_by_key(sheet_id)
worksheet = spreadsheet.sheet1


def add_to_table(rows: list):
    """Экспорт участников из бд в гугл таблицу
    :returns `int`"""

    vk_values = worksheet.col_values(1)
    positive = 0
    negative = 0
    for row in rows:
        if str(row[0]) not in vk_values:
            worksheet.append_row(values=row)
            positive += 1
        else:
            negative += 1
    return positive, negative
