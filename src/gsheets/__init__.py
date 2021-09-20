import gspread

google_client = gspread.service_account(filename=r"utils\gsheets_credentials.json")
sheet = google_client.open_by_key('12qQo4thV3p_q2_b2uHPcsGA9LZcBaGqOmbeb2bCPyz4')
worksheet = sheet.sheet1


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
