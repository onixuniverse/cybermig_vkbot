import os

import vk_api
from dotenv import load_dotenv
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from src import keyboards, db, gsheets, logger, threading
from src.modules.registration import user_registration

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

            logger.debug(f"{positive} добавлено в таблицу. {negative} уже есть в таблице.")

    def message_wait(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                start_words = ["привет", "начать", "start"]
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
                                f"информацию.\n\n📄 Главная страница – чтобы перейти дальше. "
                    self.send_msg(event.user_id, hello_msg, keyboards.to_main_page)

                # Главная страница
                elif event.message.lower() in main_page_words:
                    main_page_msg = f"{info_page_msg}"
                    self.send_msg(event.user_id, main_page_msg, keyboards.default)

                # Информационная страница
                elif event.message.lower() in info_page_words:
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
                    self.export_users(event)

                # Регистрация пользователей в проекте
                elif event.message.lower() in reg_page_words:
                    threading.create_thread(user_registration , (event.user_id,))
