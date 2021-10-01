import random
import string

from vk_api.longpoll import VkEventType

from src import db, logger, keyboards, gmail


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

        reg_msg_1 = "Сейчас, скажи мне сколько тебе лет?"
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

        reg_msg_4 = "Так держать! 🎉 Ты прошел первый этап регистрации.\n Теперь я отправлю тебе несколько " \
                    "файлов, которые тебе нужно распечатать, заполнить и отправить на почту скан или фотографию." \
                    "\nТакже, тебе нужна медицинская справка о допуске к спортивным занятиям, её ты можешь взять " \
                    "у врача-педиатра или спросить про неё в регистратуре твоей больницы.\n\n ❗ Но! Укажи в ТЕМЕ " \
                    "сообщения код, который я пришлю тебе позже. "
        self.send_msg(user_id, reg_msg_4, keyboards.ready)

        reg_file_msg = "📄 Первый файл – https://docs.google.com/document/d/1H3vmFrpMDufeaM0c0Yh5Z54Au5PtvXpz" \
                       "/edit?usp=sharing&ouid=108319410384893119199&rtpof=true&sd=true\n" \
                       "📄 Второй файл – https://docs.google.com/document/d/19WhOYSJieVnCnh2P0Q7iEOB8Wvj8qHQS" \
                       "/edit?usp=sharing&ouid=108319410384893119199&rtpof=true&sd=true\n" \
                       "📄 Третий файл – https://docs.google.com/document/d/17dG2x6Yua" \
                       "-EXv2vu9TbZ5k9HnwX7Hc0nWHvVJ6q29g0/edit?usp=sharing "
        self.send_msg(user_id, reg_file_msg, keyboards.ready)

        reg_msg_code = f"Почта: {self.email_address}\n{code} – этот код тебе нужно вставить в поле ТЕМА в " \
                       f"сообщении вместе с фотографиями или сканом на почту.\n\nКак отправишь жми \"👍 Готово!\" "
        self.send_msg(user_id, reg_msg_code, keyboards.ready)

        check_inbox_msg = False
        while not check_inbox_msg:
            check_inbox_msg = self.wait_ready_msg(user_id)
            if check_inbox_msg:
                reg_msg_5 = "Отлично! Твоя регистрация завершена!\nПозже с тобой свяжутся организаторы и всё " \
                            "подробно расскажут. Если у тебя есть какие либо вопросы – заходи во вкладку помощь! "
                self.send_msg(user_id, reg_msg_5, keyboards.to_main_page)
                return
            elif not check_inbox_msg:
                err_msg_reg_5 = "Хмм... Похоже что-то не так. Я не вижу твоего сообщения. Свяжись с технической " \
                                "поддержкой. "
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
