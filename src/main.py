import os
import random
import string

import vk_api
from dotenv import load_dotenv
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from src import keyboards, db, gsheets, logger, threading, gmail

load_dotenv()


class Bot:
    def __init__(self, api_token):
        self.conn = db.connect()
        self.cur = self.conn.cursor()

        self.vk_session = vk_api.VkApi(token=api_token)
        self.long_poll = VkLongPoll(self.vk_session)
        self.vk_upload = VkUpload(self.vk_session)
        self.vk = self.vk_session.get_api()

        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.admin_list_id = [6700376, 219871037]

    def start(self):
        logger.info("Бот начал работу.")

        db.check(self.conn, self.cur)
        self.message_wait()

    def send_msg(self, user_id: int, message: str, keyboard=None):
        """Отправляет сообщение пользователю"""
        if keyboard is None:
            keyboard = '{"buttons": [], "one_time": true}'
        self.vk.messages.send(peer_id=user_id, message=message, random_id=get_random_id(), keyboard=keyboard)

    def get_user_name(self, user_id: int):
        """Возвращает имя пользователя
        :return `str`"""
        return self.vk.users.get(user_id=user_id)[0]

    def export_users(self, event):
        if event.user_id in self.admin_list_id:
            rows = db.fetchall(self.cur, "SELECT * FROM users")
            positive, negative = gsheets.add_to_table(rows)

            msg = f"Добавлено пользователей: {positive}\nУже присутствуют в таблице: {negative}"
            self.send_msg(event.user_id, msg)

            logger.info(f"{positive} добавлено в таблицу. {negative} уже есть в таблице.")

    def mailing(self, event):
        if event.user_id in self.admin_list_id:
            msg_text = event.text[11::]
            rows = db.fetchall(self.cur, "SELECT vk_user_id FROM users")
            for id in rows:
                self.vk.messages.send(peer_id=id[0], message=msg_text, random_id=get_random_id())

    def message_wait(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                start_words = ["привет", "начать", "start", "здравствуйте"]
                main_page_words = ["📄 главная страница", "главная страница", "главная", "📄 на главную", "на главную"]
                info_page_words = ["ℹ️ информация", "информация", "инфо"]
                reg_page_words = ["💁 регистрация", "регистрация", "рег"]

                info_page_msg = "Проект Школьная лига «КиберМиг» будет состоять из цикла мероприятий, направленных " \
                                "на организацию киберспортивных событий детей и подростков, проживающих в городе " \
                                "Кургане. Проект будет включать в себя четыре направления: теоретическая часть (" \
                                "история киберспорта, основные направления, мастер – классы от спортсменов), " \
                                "физическая подготовка (мастер-классы от КМС и спортивные игры), киберспортивные " \
                                "турниры по играм, участие команд во Всероссийской интеллектуально-киберспортивной " \
                                "лиге и Всероссийской киберспортивной школьной лиге РДШ."

                # Приветствие
                if event.message.lower() in start_words:
                    hello_msg = f"Привет, {self.get_user_name(event.user_id)['first_name']}! Я Бот, отвечающий за " \
                                f"регистрацию участников, ответы на часто задаваемые вопросы, и рассказываю основную " \
                                f"информацию.\n\n📄 На главную – чтобы перейти дальше. "
                    self.send_msg(event.user_id, hello_msg, keyboards.to_main_page)

                # Главная страница
                elif event.message.lower() in main_page_words:
                    main_page_msg = "Главное меню"
                    self.send_msg(event.user_id, main_page_msg, keyboards.main_menu)

                # Информационная страница
                elif event.message.lower() in info_page_words:
                    self.send_msg(event.user_id, info_page_msg, keyboards.to_main_page)

                # Страница помощи
                elif event.message == "🆘 Помощь" or event.message.lower() == "помощь":
                    help_msg = "1. ⌨️ Команды – список команд бота.\n2. 💬 Обратная связь – помощь напрямую с " \
                               "организаторами проекта.\n3. ❓ ЧаВо – частозадаваемые вопросы."
                    self.send_msg(event.user_id, help_msg, keyboards.help_page)

                # Команды
                elif event.message == "⌨️ Команды" or event.message.lower() == "команды":
                    cmd_msg = "1. ℹ️ Информация – основная информация о проекте.\n2. 💁 Регистрация – регистрация " \
                              "пользователей в проекте.\n3. ⌨️ Команды – список команд бота.\n4. 💬 Обратная связь – " \
                              "помощь напрямую с организаторами проекта.\n5. ❓ ЧаВо – частозадаваемые вопросы.\n6. 🆘 " \
                              "Помощь – помощь. "
                    self.send_msg(event.user_id, cmd_msg, keyboards.help_page)

                # Обратная связь
                elif event.message == "💬 Обратная связь" or event.message.lower() == "обратная связь":
                    callback_msg = "• Марина Александровна Иванова\n" \
                                   "VK: https://vk.com/marinaangelivanova\n" \
                                   "Instagram: https://www.instagram.com/iteacherma/\n\n" \
                                   "• Дарья Андреевна Мезенцева" \
                                   "\nVK: https://vk.com/aleesk\n" \
                                   "Instagram: https://www.instagram.com/teach_hist/\n\n" \
                                   "По поводу ошибок бота писать на почту: warofmyhome@gmail.com"
                    self.send_msg(event.user_id, callback_msg, keyboards.help_page)

                # ЧаВо
                elif event.message == "❓ ЧаВо" or event.message == "ЧаВо":
                    faq_msg = ["1. Со скольки лет можно участвовать?\nОтвет: с 10 до 18 лет.\n\n",
                               "2. Какие документы нужны для регистрации?\nОтвет: три файл, которые предаставит бот и "
                               "справка о занятиях спортом."]  # дописать вопросы
                    self.send_msg(event.user_id, "".join(faq_msg), keyboards.help_page)

                # Админ-команды
                elif "//экспорт" in event.message:
                    self.export_users(event)

                elif "//рассылка" in event.message:
                    self.mailing(event)

                # Регистрация пользователей в проекте
                elif event.message.lower() in reg_page_words:
                    threading.create_thread(self.user_registration, (event.user_id,))

    def user_registration(self, user_id: int):
        """Регистрация пользователя в системе"""
        result = db.fetchone(self.cur, "SELECT * FROM users WHERE vk_user_id = ?", (user_id,))
        if not result:
            reg_msg_0 = "Твоя регистрация в проекте начата, так держать! 😌\n\nДля начала, напиши своё ФИО в одном " \
                        "сообщении, но помни, что с одного аккаунта ВК можно зарегистрироваться ТОЛЬКО один " \
                        "раз!\n\nПиши ТОЛЬКО своё ФИО, так как оно будет занесено в форму регистрации и изменить его " \
                        "уже будет нельзя!"
            self.send_msg(user_id, reg_msg_0)
            user_full_name = self.wait_full_name_from_user(user_id)
            logger.info(f"{user_id} начал регистрацию.")

            reg_msg_1 = "Сколько тебе лет?"
            self.send_msg(user_id, reg_msg_1)
            user_age = self.wait_age_from_user(user_id)

            reg_msg_2 = "Теперь напиши полное название своего учебного заведения.\n\nПример: МБОУ \"СОШ\" №49 г.Кургана"
            self.send_msg(user_id, reg_msg_2)
            user_educational_institution = self.wait_educational_institution_from_user(user_id)

            reg_msg_3 = "Итак, теперь мне нужно знать в каком классе ты учишься, напиши номер и букву СЛИТНО."
            self.send_msg(user_id, reg_msg_3)
            user_class = self.wait_class_from_user(user_id)

            code = ''.join(random.sample(string.ascii_uppercase, k=6))

            db.execute(self.conn, self.cur, "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (user_id, user_full_name[0], user_full_name[1], user_full_name[2], user_age,
                        user_educational_institution, user_class, code))

            reg_msg_4 = "Так держать! 🎉 Ты прошел первый этап регистрации.\n\n Теперь я отправлю тебе несколько " \
                        "файлов, которые тебе нужно распечатать, заполнить и отправить на почту скан или фотографию." \
                        "\n\n ❗ Но! Укажи в ТЕМЕ сообщения код, который я пришлю тебе позже. "
            self.send_msg(user_id, reg_msg_4, keyboards.ready)

            file1 = "https://docs.google.com/document/d/19WhOYSJieVnCnh2P0Q7iEOB8Wvj8qHQS/edit?usp=sharing&ouid=108319410384893119199&rtpof=true&sd=true"
            file2 = "https://docs.google.com/document/d/17dG2x6Yua-EXv2vu9TbZ5k9HnwX7Hc0nWHvVJ6q29g0/edit?usp=sharing"
            file3 = "https://docs.google.com/document/d/1-VQ8mGoA8tqE4gLIWQxCy0kMWWNQqDFA/edit?usp=sharing&ouid=108319410384893119199&rtpof=true&sd=true"
            reg_file_msg = f"📄 Первый файл – {file1}\n" \
                           f"📄 Второй файл – {file2}\n" \
                           f"📄 Третий файл – {file3}"
            self.send_msg(user_id, reg_file_msg, keyboards.ready)

            reg_msg_code = f"Почта: {self.email_address}\n{code} – этот код тебе нужно вставить в поле ТЕМА в " \
                           f"сообщении вместе с фотографиями или сканом на почту.\n\nКак отправишь жми \"👍 Готово!\"" \
                           f"\n\nОтвет поступит в течении суток. "
            self.send_msg(user_id, reg_msg_code, keyboards.ready)

            check_inbox_msg = False
            while not check_inbox_msg:
                check_inbox_msg = self.wait_ready_msg(user_id)
                if check_inbox_msg:
                    reg_msg_5 = "Отлично! Твоя регистрация завершена!\nПозже с тобой свяжутся организаторы и всё " \
                                "подробно расскажут. Если у тебя есть какие либо вопросы – заходи во вкладку помощь! "
                    self.send_msg(user_id, reg_msg_5, keyboards.to_main_page)
                    return
                else:
                    err_msg_reg_5 = "Хмм... Похоже что-то не так. Я не вижу твоего сообщения. Попробуй ещё раз или " \
                                    "свяжись с технической поддержкой."
                    self.send_msg(user_id, err_msg_reg_5, keyboards.ready)
        else:
            msg = "Похоже, что твой аккаунт уже зарегистрирован в проекте.\nС одного аккаунта можно " \
                  "зарегистрироваться ТОЛЬКО один раз!"
            self.send_msg(user_id, msg, keyboards.to_main_page)
            return

    def wait_full_name_from_user(self, user_id: int):
        """Ожидание ответа пользователя на: запрос ФИО"""
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.peer_id == user_id:
                full_name = event.message.split()
                if len(full_name) == 3:
                    return full_name
                else:
                    error_name_msg = "Попробуй ещё раз.\n\nПример: Иванов Иван Иванович"
                    self.send_msg(event.user_id, error_name_msg)

    def wait_age_from_user(self, user_id: int):
        """Ожидание ответа пользователя на: запрос возраста
        :return `str`"""
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.peer_id == user_id:
                return event.message

    def wait_educational_institution_from_user(self, user_id: int):
        """Ожидание ответа пользователя на: запрос ОУ
        :return `str`"""
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.peer_id == user_id:
                return event.message

    def wait_class_from_user(self, user_id: int):
        """Ожидание ответа пользователя на: запрос учебного класса
        :return `str`"""
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.peer_id == user_id:
                return event.message

    def wait_ready_msg(self, user_id: int):
        """Ожидание ответа пользователя на: запрос готовности
        :return `bool`"""
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.peer_id == user_id:
                email_msgs = gmail.get_inbox()
                unique_code = ''.join(db.fetchone(self.cur, "SELECT code FROM users WHERE vk_user_id = ?", (user_id,)))
                if email_msgs:
                    for msg in email_msgs:
                        if msg['title'] == unique_code:
                            return True
                return False
