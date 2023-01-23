import os

from pyrogram import types, Client, filters, enums
from db import *
from datetime import date
import json


api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

app = Client(
    "ivanovogidbot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)
admins = [965840090]


@app.on_message(filters.command(['main_menu', 'start']))
def send_main_menu(bot, message, new_message=True):
    to_sights = types.InlineKeyboardButton('К достопримечательностям', callback_data=to_callback_data({"section": 'to_location'}))
    to_add_new = types.InlineKeyboardButton('Добавить новое' if message.chat.id in admins else 'Хочу предложить что-то свое', callback_data=to_callback_data({"section": 'to_add_new'}))
    to_about = types.InlineKeyboardButton('О боте', callback_data=to_callback_data({"section": 'to_about'}))

    markup = types.InlineKeyboardMarkup([[to_sights], [to_add_new], [to_about]])

    if new_message:
        bot.send_message(message.chat.id,
            'Привет! Я бот, который может рассказать тебе о достопримечательностях города Иваново и его области. Надеюсь, ты узнаешь много нового! Погнали ;)',
            reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.id, text=
            'Привет! Я бот, который может рассказать тебе о достопримечательностях города Иваново и его области. Надеюсь, ты узнаешь много нового! Погнали ;)',
            reply_markup=markup)


def send_location(bot, call):
    city = types.InlineKeyboardButton('Иваново', callback_data=to_callback_data({"section": 'to_categories', "city": True, "page": 0}))
    region = types.InlineKeyboardButton('Область', callback_data=to_callback_data({"section": 'to_categories', "city": False, "page": 0}))
    to_main_menu = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_main_menu'}))
    markup = types.InlineKeyboardMarkup([[city], [region], [to_main_menu]])

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Давай определимся с местоположением', reply_markup=markup)


def send_categories(bot, call, city, page):
    categories = list(filter(lambda category: list(filter(lambda sight: sight.city == city, category.sights))!=[],Category.select()))[page*5:]

    markup = types.InlineKeyboardMarkup([])

    buttons = []

    for i in range(min(5, len(categories))):
        buttons.append(types.InlineKeyboardButton(categories[i].name, callback_data=to_callback_data({"section": 'to_sights', "category_id": categories[i].id, "city": city, "page": 0, 'categories_page': page, "to_delete": None})))

    if page == 0:
        previous_button = types.InlineKeyboardButton('', callback_data='null')
    else:
        previous_button = types.InlineKeyboardButton('<<', callback_data=to_callback_data({"section": 'to_categories', "city": city, "page": page-1}))

    if len(categories) > 5:
        next_button = types.InlineKeyboardButton('>>', callback_data=to_callback_data({"section": 'to_categories', "city": city, "page": page+1}))
    else:
        next_button = types.InlineKeyboardButton('', callback_data='null')

    to_location = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_location'}))

    for button in buttons:
        markup.inline_keyboard.append([button])
    markup.inline_keyboard.append([previous_button, next_button])
    markup.inline_keyboard.append([to_location])

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Выбери категорию', reply_markup=markup)


def send_sights(bot, call, category_id, city, page, categories_page):
    sights = Sight.select().join(Category).where(Sight.category.id == category_id).where(Sight.city == city)[page*5:]

    markup = types.InlineKeyboardMarkup([])

    buttons = []

    for i in range(min(5, len(sights))):
        buttons.append(types.InlineKeyboardButton(sights[i].name, callback_data=to_callback_data({"section": 'to_sight', "sight_id": sights[i].id, "categories_page": categories_page, "sights_page": page})))

    if page == 0:
        previous_button = types.InlineKeyboardButton('', callback_data='null')
    else:
        previous_button = types.InlineKeyboardButton('<<', callback_data=to_callback_data({"section": 'to_sights', "categories_page": categories_page, "category_id": category_id, "city": city, "page": page-1, "to_delete": None}))

    if len(sights) > 5:
        next_button = types.InlineKeyboardButton('>>', callback_data=to_callback_data({"section": 'to_sights', "categories_page": categories_page, "category_id": category_id, "city": city, "page": page+1, "to_delete": None}))
    else:
        next_button = types.InlineKeyboardButton('', callback_data='null')

    to_location = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_categories', "page": categories_page, "city": city}))

    for button in buttons:
        markup.inline_keyboard.append([button])
    markup.inline_keyboard.append([previous_button, next_button])
    markup.inline_keyboard.append([to_location])

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Это все, что у меня есть', reply_markup=markup)


def send_sight(bot, call, sight_id, categories_page, sights_page):
    sight = Sight.get_by_id(sight_id)

    text = f'**{sight.name}**\n' + f'`{sight.address}`\n' + sight.description
    photos = [types.InputMediaPhoto(media=sight.imgs[0], caption=text, parse_mode=enums.ParseMode.MARKDOWN)]
    for i in range(1, len(sight.imgs)):
        photos.append(types.InputMediaPhoto(media=sight.imgs[i]))

    messages = bot.send_media_group(call.message.chat.id, photos)
    messages_id = list(map(lambda message: message.id, messages))

    to_confirm_delete_sight = types.InlineKeyboardButton('Удалить', callback_data=to_callback_data({"section": 'to_confirm_delete_sight', "sight_id": sight_id, "categories_page": categories_page, "sights_page": sights_page, "to_delete": messages_id}))
    to_sights = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_sights', "categories_page": categories_page, "page": sights_page, "category_id": sight.category.id, "city": sight.city, "to_delete": messages_id}))
    markup_user = types.InlineKeyboardMarkup([[to_sights]])
    markup_admin = types.InlineKeyboardMarkup([[to_confirm_delete_sight], [to_sights]])

    if call.message.chat.id in admins:
        bot.send_message(call.message.chat.id, text='Действуйте, босс', reply_markup=markup_admin)
        bot.delete_messages(call.message.chat.id, call.message.id)
    else:
        bot.send_message(call.message.chat.id, text='Не сказать, что у тебя большой выбор', reply_markup=markup_user)
        bot.delete_messages(call.message.chat.id, call.message.id)


def send_confirm_delete_sight(bot, call, sight_id, categories_page, sights_page):
    to_sights = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({'section': 'to_sight', 'sight_id': sight_id, 'categories_page': categories_page, 'sights_page': sights_page}))
    confirm_delete = types.InlineKeyboardButton('Удалить', callback_data=to_callback_data({'section': 'to_delete_sight', 'sight_id': sight_id, 'categories_page': categories_page, 'sights_page': sights_page}))
    markup = types.InlineKeyboardMarkup([[confirm_delete], [to_sights]])
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Вы уверены, что ходите удалить достопримечательность «' + Sight.get_by_id(sight_id).name + '»?', reply_markup=markup)


def delete_sight(bot, call, sight_id, categories_page, sights_page):
    sight = Sight.get_by_id(sight_id)
    category_id = sight.category.id
    city = sight.city
    sight.delete_instance()
    send_sights(bot, call, category_id, city, sights_page, categories_page)


def send_add_new(bot, call):
    # markup = types.InlineKeyboardMarkup()
    # to_main_menu = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_main_menu'}))
    # markup.row(to_main_menu)
    text = "Пришлите достопримечательность, которую хотели бы увидеть в этом боте.\nЧтобы я вас понял, это необходимо сделать ответом на данное сообщение.\nУчтите, что сообщение должно содержать хотя бы одну фотографию и иметь вид\n<Название>\n<Местоположение>\n<Иваново/Область>\n<Точное название категории>\n<Описание>" if call.message.chat.id in admins else "Пришлите достопримечательность, которую хотели бы увидеть в этом боте.\nУчтите, что сообщение должно содержать хотя бы одну фотографию и иметь вид\n<Название>\n<Местоположение>\n<Описание>"
    to_main_menu = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_main_menu'}))
    markup = types.InlineKeyboardMarkup([[to_main_menu]])
    sent = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=text, reply_markup=markup)
    # bot.register_next_step_handler(sent, create_new_sight, **{'bot': bot})


def send_about(bot, call):
    to_source_code = types.InlineKeyboardButton('Исходный код', url='github.com')
    to_main_menu = types.InlineKeyboardButton('Назад', callback_data=to_callback_data({"section": 'to_main_menu'}))
    markup = types.InlineKeyboardMarkup([[to_source_code], [to_main_menu]])

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=
        'Вы не поверите, но я школьный проект одного 11-классника. Исходный код открыт, все дела',
        reply_markup=markup)


@app.on_callback_query()
def callback_handler(bot, call):
    data = from_callback_data(call.data)
    print('\n' + str(call.message.chat.id) + ' has pressed ' + json.dumps(data) + '\n')
    if data['section'] == 'to_main_menu':
        send_main_menu(bot, call.message, False)
        return
    if data['section'] == 'to_location':
        send_location(bot, call)
        return
    if data['section'] == 'to_categories':
        send_categories(bot, call, data['city'], data['page'])
        return
    if data['section'] == 'to_sights':
        if data['to_delete'] is not None:
            bot.delete_messages(call.message.chat.id, data['to_delete'])
        send_sights(bot, call, data['category_id'], data['city'], data['page'], data['categories_page'])
        return
    if data['section'] == 'to_sight':
        send_sight(bot, call, data['sight_id'], data['categories_page'], data['sights_page'])
        return
    if data['section'] == 'to_confirm_delete_sight':
        if data['to_delete'] is not None:
            bot.delete_messages(call.message.chat.id, data['to_delete'])
        send_confirm_delete_sight(bot, call, data['sight_id'], data['categories_page'], data['sights_page'])
        return
    if data['section'] == 'to_delete_sight':
        delete_sight(bot, call, data['sight_id'], data['categories_page'], data['sights_page'])
        return
    if data['section'] == 'to_add_new':
        send_add_new(bot, call)
        return
    if data['section'] == 'to_about':
        send_about(bot, call)
        return


@app.on_message(~filters.command(['start', 'main_menu']))
async def error_404(bot, message):
    print('##### MESSAGE IN FUNCTION ERROR_404 #####\n\n')
    print(message)
    print('\n\n#####')

    if message.media_group_id is not None and message.caption is None:
        return

    if message.reply_to_message is not None and message.reply_to_message.from_user.username == 'ivanovogidbot':
        message_text_is_right = False
        if message.chat.id in admins:
            message_text_is_right = message.reply_to_message.text == "Пришлите достопримечательность, которую хотели бы увидеть в этом боте.\nЧтобы я вас понял, это необходимо сделать ответом на данное сообщение.\nУчтите, что сообщение должно содержать хотя бы одну фотографию и иметь вид\n<Название>\n<Местоположение>\n<Иваново/Область>\n<Точное название категории>\n<Описание>"
        else:
            message_text_is_right = message.reply_to_message.text == "Пришлите достопримечательность, которую хотели бы увидеть в этом боте.\nУчтите, что сообщение должно содержать хотя бы одну фотографию и иметь вид\n<Название>\n<Местоположение>\n<Описание>"
        if message_text_is_right:
            await create_new_sight(bot, message)
            return

    to_main_menu = types.InlineKeyboardButton('В главное меню', callback_data=to_callback_data({"section": 'to_main_menu'}))
    markup = types.InlineKeyboardMarkup([[to_main_menu]])
    await bot.send_message(message.chat.id, 'Боюсь, я тебя не понимаю', reply_markup=markup)


def to_callback_data(uncompressed_data):  # telegram can't store big strings in callback_data (>64 bytes), so i need to compress it
    compressed_data = []
    section = uncompressed_data['section']
    sections_map = {'to_main_menu': 'mm', 'to_location': 'l', 'to_categories': 'c', 'to_sights': 'ss', 'to_sight': 's', 'to_add_new': 'an', "to_admin_options": 'ao', 'to_about': 'a', 'to_confirm_delete_sight': 'cds', 'to_delete_sight': 'ds'}
    compressed_data.append(sections_map[section])
    if section == 'to_categories':
        compressed_data.extend([int(uncompressed_data['city']), uncompressed_data['page']])
    if section == 'to_sights':
        compressed_data.extend([uncompressed_data['category_id'], int(uncompressed_data['city']), uncompressed_data['page'], uncompressed_data['categories_page'], uncompressed_data['to_delete']])
    if section == 'to_sight':
        compressed_data.extend([uncompressed_data['sight_id'], uncompressed_data['sights_page'], uncompressed_data['categories_page']])
    if section == 'to_confirm_delete_sight':
        compressed_data.extend([uncompressed_data['sight_id'], uncompressed_data['sights_page'], uncompressed_data['categories_page'], uncompressed_data['to_delete']])
    if section == 'to_delete_sight':
        compressed_data.extend([uncompressed_data['sight_id'], uncompressed_data['sights_page'], uncompressed_data['categories_page']])
    return json.dumps(compressed_data, separators=(',', ':'))


def from_callback_data(compressed_data):
    compressed_data = json.loads(compressed_data)
    uncompressed_data = {}
    sections_map = {'mm': 'to_main_menu', 'l': 'to_location', 'c': 'to_categories', 'ss': 'to_sights', 's': 'to_sight', 'an': 'to_add_new', 'ao': 'to_admin_options', 'a': 'to_about', 'cds': 'to_confirm_delete_sight', 'ds': 'to_delete_sight'}
    uncompressed_data['section'] = sections_map[compressed_data[0]]
    if uncompressed_data['section'] == 'to_categories':
        uncompressed_data['city'] = bool(compressed_data[1])
        uncompressed_data['page'] = compressed_data[2]
    if uncompressed_data['section'] == 'to_sights':
        uncompressed_data['category_id'] = compressed_data[1]
        uncompressed_data['city'] = bool(compressed_data[2])
        uncompressed_data['page'] = compressed_data[3]
        uncompressed_data['categories_page'] = compressed_data[4]
        uncompressed_data['to_delete'] = compressed_data[5]
    if uncompressed_data['section'] == 'to_sight':
        uncompressed_data['sight_id'] = compressed_data[1]
        uncompressed_data['sights_page'] = compressed_data[2]
        uncompressed_data['categories_page'] = compressed_data[3]
    if uncompressed_data['section'] == 'to_confirm_delete_sight':
        uncompressed_data['sight_id'] = compressed_data[1]
        uncompressed_data['sights_page'] = compressed_data[2]
        uncompressed_data['categories_page'] = compressed_data[3]
        uncompressed_data['to_delete'] = compressed_data[4]
    if uncompressed_data['section'] == 'to_delete_sight':
        uncompressed_data['sight_id'] = compressed_data[1]
        uncompressed_data['sights_page'] = compressed_data[2]
        uncompressed_data['categories_page'] = compressed_data[3]
    return uncompressed_data


async def parse_message(message):
    try:
        strings = message.caption.split('\n')
        images_id = [message.photo.file_id]
        if message.media_group_id is not None:
            images_id = [message_with_image.photo.file_id for message_with_image in await app.get_media_group(message.chat.id, message.id)]
        if message.chat.id in admins:
            parsed_message = {'name': strings[0], 'address': strings[1], 'city': strings[2].lower() == 'иваново', 'category': Category.get_or_create(name=strings[3])[0], 'description': '\n'.join([*strings[4:]]), 'imgs': images_id, 'date_modified': date.today()}
        else:
            parsed_message = {'name': strings[0], 'address': strings[1], 'description': '\n'.join([strings[2], *strings[3:]]), 'imgs': images_id}
    except Exception as e:
        print('##### EXCEPTION WHILE PARSING MESSAGE #####\n\n')
        print(e)
        print('\n\n#####')
        parsed_message = None
    print('##### PARSED MESSAGE #####\n\n')
    print(parsed_message)
    (print('\n\n#####'))
    return parsed_message


async def create_new_sight(bot, message):
    if message.caption == '/main_menu' or message.text == '/main_menu':
        send_main_menu(message)
        return
    parsed_message = await parse_message(message)
    if parsed_message is not None:
        if message.chat.id in admins:
            sight = Sight.create(**parsed_message)
            sight.save()

            to_main_menu = types.InlineKeyboardButton('Обратно в главное меню', callback_data=to_callback_data({"section": 'to_main_menu'}))
            markup = types.InlineKeyboardMarkup([[to_main_menu]])
            await bot.send_message(message.chat.id, 'Отлично! Я сохранил эту достопримечательность', reply_markup=markup)
        else:
            to_forward = message.id
            if message.media_group_id is not None:
                to_forward = list(map(lambda m: m.id, await app.get_media_group(message.chat.id, message.id)))
            await bot.forward_messages(admins[0], message.chat.id, to_forward)

            to_main_menu = types.InlineKeyboardButton('Обратно в главное меню', callback_data=to_callback_data({"section": 'to_main_menu'}))
            markup = types.InlineKeyboardMarkup([[to_main_menu]])
            await bot.send_message(message.chat.id, 'Отлично! Я переслал твое сообщение админу, рано или поздно он обязательно его посмотрит', reply_markup=markup)
    else:
        to_add_new = types.InlineKeyboardButton('Я хочу попытаться еще раз', callback_data=to_callback_data({"section": 'to_add_new'}))
        to_main_menu = types.InlineKeyboardButton('Я сдаюсь', callback_data=to_callback_data({'section': 'to_main_menu'}))
        markup = types.InlineKeyboardMarkup([[to_add_new], [to_main_menu]])
        await bot.send_message(message.chat.id, 'Боюсь, я тебя не понимаю', reply_markup=markup)


if __name__ == '__main__':
    print('Working...')
    app.run()
