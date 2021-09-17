import random
import sqlite3
import string

import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from src import keyboards, db, gmail
from src.threadings import create_thread


class Bot:
    def __init__(self, api_token):
        self.conn = sqlite3.connect(r"./db.sqlite3", check_same_thread=False)
        self.cur = self.conn.cursor()

        self.vk_session = vk_api.VkApi(token=api_token)
        self.long_poll = VkLongPoll(self.vk_session)
        self.vk_upload = VkUpload(self.vk_session)
        self.vk = self.vk_session.get_api()

        self.email_address = "cybermig.league@gmail.com"
        self.admin_list_id = [6700376, 219871037]

    def start(self):
        print("Бот запущен!")

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

    def user_registration(self, user_id: int):
        """Регистрация пользователя в проекте"""
        result = db.fetchone(self.cur, "SELECT * FROM users WHERE vk_user_id = ?", (user_id,))
        if not result:
            reg_msg_0 = "Твоя регистрация в проекте начата, так держать! 😌\n\nДля начала, напиши своё ФИО в одном " \
                        "сообщении, но помни, что с одного аккаунта ВК можно зарегистрироваться ТОЛЬКО один " \
                        "раз!\n\nПиши ТОЛЬКО своё ФИО, так как оно будет занесено в форму регистрации и изменить его " \
                        "уже будет нельзя! "
            self.send_msg(user_id, reg_msg_0)

            user_full_name = self.wait_full_name_from_user(user_id)

            reg_msg_1 = "Теперь напиши полное название своего учебного заведения.\n\nПример: МБОУ \"СОШ\" №49 г.Кургана"
            self.send_msg(user_id, reg_msg_1)

            user_educational_institution = self.wait_educational_institution_from_user(user_id)

            reg_msg_2 = "Итак, теперь мне нужно знать в каком классе ты учишься, напиши номер и букву СЛИТНО."
            self.send_msg(user_id, reg_msg_2)

            user_class = self.wait_class_from_user(user_id)

            CODE = ''.join(random.sample(string.ascii_uppercase, k=6))

            db.execute(self.conn, self.cur, "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user_id, user_full_name[0], user_full_name[1], user_full_name[2],
                        user_educational_institution, user_class, CODE))

            reg_msg_3 = "Так держать! 🎉 Ты прошел первый этап регистрации.\n Теперь я отправлю тебе несколько " \
                        "файлов, которые тебе нужно распечатать, заполнить и отправить на почту скан или фотографию." \
                        "\nТакже, тебе нужна медицинская справка о допуске к спортивным занятиям, её ты можешь взять " \
                        "у врача-педиатра или спросить про неё в регистратуре твоей больницы.\n\n ❗ Но! Укажи в ТЕМЕ " \
                        "сообщения код, который я пришлю тебе позже. "
            self.send_msg(user_id, reg_msg_3, keyboards.ready)

            reg_file_msg = "📄 Первый файл – https://docs.google.com/document/d/1H3vmFrpMDufeaM0c0Yh5Z54Au5PtvXpz" \
                           "/edit?usp=sharing&ouid=108319410384893119199&rtpof=true&sd=true\n 📄 Второй файл – " \
                           "https://docs.google.com/document/d/19WhOYSJieVnCnh2P0Q7iEOB8Wvj8qHQS/edit?usp=sharing" \
                           "&ouid=108319410384893119199&rtpof=true&sd=true "
            self.send_msg(user_id, reg_file_msg, keyboards.ready)

            reg_msg_code = f"Почта: {self.email_address}\n{CODE} – этот код тебе нужно вставить в поле ТЕМА в " \
                           f"сообщении вместе с фотографиями или сканом на почту.\n\nКак отправишь жми \"👍 Готово!\" "
            self.send_msg(user_id, reg_msg_code, keyboards.ready)

            check_inbox_msg = False
            while not check_inbox_msg:
                check_inbox_msg = self.wait_ready_msg(user_id)
                if check_inbox_msg:
                    reg_msg_4 = "Отлично! Твоя регистрация завершена!\nПозже с тобой свяжутся организаторы и всё " \
                                "подробно расскажут. Если у тебя есть какие либо вопросы – заходи во вкладку помощь! "
                    self.send_msg(user_id, reg_msg_4, keyboards.to_main_page)
                    return
                elif not check_inbox_msg:
                    err_msg_reg_4 = "Хмм... Похоже что-то не так. Я не вижу твоего сообщения. Свяжись с технической " \
                                    "поддержкой. "
                    self.send_msg(user_id, err_msg_reg_4, keyboards.ready)

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
                unique_code = ''.join(db.fetchone(self.cur, "SELECT CODE FROM users WHERE vk_user_id = ?", (user_id,)))
                if email_msgs:
                    for msg in email_msgs:
                        if msg['title'] == unique_code:
                            return True
                    return False

    def admin_page(self, event):
        if event.user_id in self.admin_list_id:
            row = db.fetchall(self.cur, "SELECT * FROM users")
            print(row)

    def message_wait(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                start_words = ["Привет", "привет", "ПРИВЕТ", "Начать", "Start"]
                main_page_words = ["📄 Главная страница", "Главная страница", "главная страница", "Главная", "главная",
                                   "📄 На главную", "На главную", "на главную"]
                info_page_words = ["ℹ️ Информация", "Информация", "информация", "Инфо", "инфо"]
                reg_page_words = ["💁 Регистрация", "Регистрация", "регистрация", "рег", "Рег"]

                info_page_msg = "Проект Школьная лига «КиберМиг» будет состоять из цикла мероприятий, направленных " \
                                "на организацию киберспортивных событий детей и подростков, проживающих в городе " \
                                "Кургане. Проект будет включать в себя четыре направления: теоретическая часть (" \
                                "история киберспорта, основные направления, мастер – классы от спортсменов), " \
                                "физическая подготовка (мастер-классы от КМС и спортивные игры), киберспортивные " \
                                "турниры по играм, участие команд во Всероссийской интеллектуально-киберспортивной " \
                                "лиге и Всероссийской киберспортивной школьной лиге РДШ."

                # Приветствие
                if event.message in start_words:
                    hello_msg = f"Привет, {self.get_user_name(event.user_id)['first_name']}! Я Бот, отвечающий за " \
                                f"регистрацию участников, ответы на часто задаваемые вопросы, и рассказываю основную " \
                                f"информацию.\n\n📄 Главная страница – чтобы перейти дальше. "
                    self.send_msg(event.user_id, hello_msg, keyboards.to_main_page)

                # Главная страница
                elif event.message in main_page_words:
                    main_page_msg = f"{info_page_msg}"
                    self.send_msg(event.user_id, main_page_msg, keyboards.default)

                # Информационная страница
                elif event.message in info_page_words:
                    self.send_msg(event.user_id, info_page_msg, keyboards.to_main_page)

                # Страница помощи
                elif event.message == "🆘 Помощь" or event.message == "Помощь":
                    help_msg = "1. ⌨️ Команды – список команд бота.\n2. 💬 Обратная связь – помощь напрямую с " \
                               "организаторами проекта.\n3. ❓ ЧаВо – частозадаваемые вопросы."
                    self.send_msg(event.user_id, help_msg, keyboards.help_page)

                # Команды
                elif event.message == "⌨️ Команды" or event.message == "Команды":
                    cmd_msg = "1. ℹ️ Информация – основная информация о проекте.\n2. 💁 Регистрация – регистрация " \
                              "пользователей в проекте.\n3. ⌨️ Команды – список команд бота.\n4. 💬 Обратная связь – " \
                              "помощь напрямую с организаторами проекта.\n5. ❓ ЧаВо – частозадаваемые вопросы.\n6. 🆘 " \
                              "Помощь – помощь. "
                    self.send_msg(event.user_id, cmd_msg, keyboards.help_page)

                # Обратная связь
                elif event.message == "💬 Обратная связь" or event.message == "Обратная связь":
                    callback_msg = "• Марина Александровна Иванова\nVK: https://vk.com/marinaangelivanova\n" \
                                   "Instagram: https://www.instagram.com/iteacherma/\n\n• Дарья Андреевна Алексеева" \
                                   "\nVK: https://vk.com/aleesk\nInstagram: https://www.instagram.com/teach_hist/ "
                    self.send_msg(event.user_id, callback_msg, keyboards.help_page)

                # ЧаВо
                elif event.message == "❓ ЧаВо" or event.message == "ЧаВо":
                    faq_msg = "Скоро здесь что-то будет..."  # дописать вопросы
                    self.send_msg(event.user_id, faq_msg, keyboards.help_page)

                # Админ-команды
                elif event.message == "//экспорт":
                    self.admin_page(event)

                # Регистрация пользователей в проекте
                elif event.message in reg_page_words:
                    create_thread(self.user_registration, (event.user_id,))
