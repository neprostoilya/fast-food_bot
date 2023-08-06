from config import *
from keyboards import *
from utils import *

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, InputMedia, LabeledPrice
import re     

storage = MemoryStorage()


class Questions(StatesGroup):
    product_category = State()
    product_name = State()
    product_price = State()
    product_info = State()
    product_photo = State()
    product_ack = State()


bot = Bot(TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start', 'help', 'about']) 
async def command_start(message: Message):
    """ Реакция бота на команды. """

    text = message.text
    match text:
        case '/start':
            await message.answer(
                f'Добро пожаловать <b>{message.from_user.first_name}</b>.\n' \
                'Вас приветствует бот доставки'
                )    
            await register_user(message)
          
        case  '/about':
            await message.answer(
                'Этот бот был создан для портфолио\n' \
                'С использованием <b>SQLAlchemy, Python, Aiogram</b>\n' \
                'Ссылка на GitHub репозиторий') # TODO вставить ссылку гита
            
        case '/help':
            await message.answer(
                'Если у вас возникли ошибки или вопросы?\n'
                f'Пишите к @neprostoilyaa'
            )

async def register_user(message: Message):
    """ Авторизация и Регистрация юзера. """
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = db_check_user(chat_id)
    if user:
        await message.answer('Авторизация прошла успешно')
        await show_main_menu(message)
    else:
        db_first_register_user(full_name=full_name, telegram_id=chat_id)

        await message.answer(
            text='Для регистрации нажмите на кнопку',
            reply_markup=generate_phone_button()
        )

@dp.message_handler(content_types=['contact']) 
async def finish_register(message: Message):
    """ Финальная регистрация юзера. """
    chat_id = message.chat.id
    phone = message.contact.phone_number
    db_finally_register_user(chat_id, phone)
    await create_cart_for_user(message)
    await message.answer('Регистрация прошла успешно')
    await show_main_menu(message)


async def create_cart_for_user(message):
    """ Создание корзинки юзера. """
    chat_id = message.chat.id
    try:
        db_create_user_cart(chat_id)
    except:
        pass


async def show_main_menu(message: Message):
    """ Главное меню. """
    await message.answer(
        text='Выберите направление:',
        reply_markup=generate_main_menu()
    )

@dp.message_handler(lambda message: '✔️ Сделать заказ' in message.text)
async def make_order(message: Message):
    """ Реакция на кнопку. """
    chat_id = message.chat.id
    await bot.send_message(chat_id, 
        text='Погнали', 
        reply_markup=back_to_main_menu()
    )
    await message.answer(
        text='Выберите категорию: ', 
        reply_markup=generate_category_menu(chat_id)
    )

@dp.message_handler(lambda message: 'Главное меню' in message.text)
async def back_to_main(message: Message):
    """ Реакция на кнопку возвращения в меню. """
    chat_id = message.chat.id
    message_id = message.message_id - 1
    await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id
    )
    await show_main_menu(message)

@dp.callback_query_handler(lambda call: 'Назад' in call.data)
async def back_to_category(call: CallbackQuery):
    """ Реакция на кнопку возвращения назад. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.edit_message_text(
        text="Выберите категорию: ",
        chat_id=chat_id, 
        message_id=message_id,
        reply_markup=generate_category_menu(chat_id)
    )
    
@dp.callback_query_handler(lambda call: 'category_' in call.data)
async def show_products(call: CallbackQuery):
    """ Вывод продуктов. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    category_id = int(call.data.split('_')[-1])
    await bot.edit_message_text(
        text='Выберите продукт:',
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=generate_products_by_category(category_id)
    )


@dp.callback_query_handler(lambda call: 'product_' in call.data)
async def show_choose_product(call: CallbackQuery):
    """ Вывод информации о продукте. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    product_id = int(call.data.split('_')[-1])
    product = db_get_product(product_id)

    try:
        user_cart = db_get_user_cart(chat_id)
        db_update_to_cart(price=product.product_price, quantity=1, cart_id=user_cart.cart_id)
        await bot.send_message(
            chat_id=chat_id,
            text='Выберите модификатор',
            reply_markup=back_to_menu()
        )

        text = f"<b>{product.product_name}</b>\n"
        text += f"<b>Ингредиенты:</b> {product.description}\n"
        text += f"<b>Цена:</b> {product.product_price} сумм"

        with open(product.image, mode='rb') as img:
            await bot.send_photo(
                chat_id = chat_id,
                photo = img,
                caption = text,
                reply_markup = generate_product_price(1)
            )
    except:
        await call.message.answer(
            "Вы еще не отправили контакт!", 
            reply_markup=generate_phone_button
        )

@dp.message_handler(regexp=r'⬅ Назад')
async def back_to_menu_products(message: Message):
    """ Реакция на кнопку назад. """
    message_id = message.message_id - 1
    await bot.delete_message(
        chat_id = message.chat.id,
        message_id = message_id
    )
    await make_order(message)

@dp.callback_query_handler(lambda call: 'action' in call.data)
async def quantity_plus_minus(call: CallbackQuery):
    """ Реакция на изменение колл-ва продукта. """
    action = call.data.split()[-1]
    message_id = call.message.message_id
    chat_id = call.from_user.id

    user_cart = db_get_user_cart(chat_id)
    cart_id = user_cart.cart_id

    product_name = call.message['caption'].split('\n')[0]
    product = db_get_product_by_name(product_name)

    if action == '+':
        db_update_to_cart(
            price = product.product_price,
            quantity = int(user_cart.total_products) + 1,
            cart_id = cart_id
        )

    elif action == '-':
        db_update_to_cart(
            price = product.product_price,
            quantity = int(user_cart.total_products) - 1,
            cart_id = cart_id
        )
        
    user_cart = db_get_user_cart(chat_id)
    text = f"<b>{product.product_name}</b>\n"
    text += f"<b>Ингредиенты:</b> {product.description}\n"
    text += f"<b>Цена:</b> {user_cart.total_price} сумм"
    
    with open(product.image, mode='rb') as img:
        await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=InputMedia(media=img, caption=text),
            reply_markup=generate_product_price(user_cart.total_products)
        )

@dp.callback_query_handler(lambda call: 'put_into_cart' in call.data)
async def put_into_cart(call: CallbackQuery):
    """ Реакция на добавление в корзинку. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_cart = db_get_user_cart(chat_id)
    cart_id = user_cart.cart_id
    total_products = user_cart.total_products
    total_price = user_cart.total_price
    product_name = call.message['caption'].split('\n')[0]

    if db_insert_or_update(cart_id, product_name, total_products, total_price):
        await bot.answer_callback_query(call.id, "Продукт добавлен")
        await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id
        )
        await make_order(call.message)
    else:
        await bot.answer_callback_query(call.id, "Количество изменено")
        await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id
        )
        await make_order(call.message)

def dont_repeat_yourself(chat_id, text):
    """ Вывод товаров в корзине. """
    cart_products = db_get_cart_products(chat_id)
    if cart_products:
        text = f'{text}\n\n'
        total_products = total_price = count = 0
        for cart_id, name, quantity, price in cart_products:
            count += 1 
            total_products += quantity
            total_price += price
            text += f'№{count}. {name}\nКоличество: {quantity}\n'
            text += f'Стоимость: {price}\n\n'

        text += f'Общее количество продуктов: {total_products}\n'
        text += f'Общая стоимость корзины: {total_price} сумм \n'
        context = (count, text, total_price, cart_id)
        return context
    
@dp.callback_query_handler(lambda call: 'cart' in call.data)
async def show_finally_cart(call: CallbackQuery):
    """ Вывод корзины юзера. """
    chat_id = call.from_user.id
    products = dont_repeat_yourself(chat_id, 'Ваша корзина')
    if products:
        _, text, *_ = dont_repeat_yourself(chat_id, 'Ваша корзина')
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=generate_cart_button(chat_id)
        )

    else: 
        await bot.edit_message_text(
            message_id=call.message.message_id,
            chat_id=chat_id,
            text='Извените но ваша корзинка пуста 🤥'
        )
        await make_order(call.message)

@dp.callback_query_handler(lambda call: 'delete' in call.data)
async def delete_cart_product(call: CallbackQuery):
    """ Удаление продукта. """
    finally_id = int(call.data.split('_')[-1])
    db_delete_product(finally_id)
    await bot.answer_callback_query(
        callback_query_id=call.id,
        text="Продукт удален!"
    )
    await show_finally_cart(call)

@dp.callback_query_handler(lambda call: 'order' in call.data)
async def create_order(call: CallbackQuery):
    """ Оплата заказа """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id
    )

    _, text, price, _ = dont_repeat_yourself(chat_id, 'Итоговый список для оплаты')
    text += "\nДоставка по городу: 10000"
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"Ваш заказ",
        description=text,
        payload="bot-defined invoice payload",
        provider_token=CLICK,
        currency='UZS',
        prices=[
            LabeledPrice(
                label="Общая стоимость",
                amount=int(price * 100)
            ),
            LabeledPrice(
                label="Доставка",
                amount=10000
            )
        ]
    )
    await bot.answer_callback_query(call.id, 'Оплачено!')
    await show_main_menu(call.message)

    chat_id = call.message.chat.id
    nickname = call.from_user.username
    phone = db_get_phone_user(chat_id)
    _, text, price, cart_id = dont_repeat_yourself(chat_id, 'Заказ')
    text += f'Ник: @{nickname}\n'
    text += f'Контакт: +{phone}'
    await bot.send_message(
        chat_id=MANAGER,
        text=text
    )
    _, order, _, _ = dont_repeat_yourself(chat_id, 'Последний заказ')
    db_insert_history_products(order, chat_id)
    db_clear_finally_cart(cart_id)

@dp.message_handler(lambda message: '📙 История' in message.text)
async def history(message: Message):
    """ Вывод истории покупок. """
    chat_id = message.from_user.id
    text = db_get_history_products(chat_id)[0][0]
    await message.answer(
        text=text
    )

@dp.message_handler(lambda message: '🛒 Корзинка' in message.text)
async def chow_cart_in_menu(message: Message):
    """ Показ корзинки товаров в меню. """
    chat_id = message.from_user.id
    products = dont_repeat_yourself(chat_id, 'Ваша корзина')
    if products:
        _, text, *_ = dont_repeat_yourself(chat_id, 'Ваша корзина')
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=generate_cart_button(chat_id)
        )

    else: 
        await bot.send_message(
            chat_id=chat_id,
            text='Извените но ваша корзинка пуста 🤥'
        )

@dp.message_handler(lambda message: '🛠️ Настройки' in message.text)
async def show_setings_button(message: Message):
    """ Настройки бота. """
    await message.answer(
        text="Выберите настройки",
        reply_markup=generate_setings_button()
    )

@dp.callback_query_handler(lambda call: 'change_phone' in call.data)
async def change_phone(call: CallbackQuery):
    """ Инструкция по смене номера """
    chat_id = call.from_user.id
    message_id = call.message.message_id
    await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id   
    )
    await bot.send_message(
        chat_id=chat_id,
        reply_markup=back_to_main_menu(),
        text='Для смены номера введите команду /change\n' \
            'Пример: /change +998999999999'
    )

@dp.callback_query_handler(lambda call: 'admin_button' in call.data)
async def admin_panel(call: CallbackQuery):
    """ Админ панель. """
    chat_id = call.from_user.id
    message_id = call.message.message_id
    if str(chat_id) == str(ADMIN):
        await start_questions(call.message)
    else:
        await bot.send_message(
            chat_id,
            text="Увы вы не Админ😥"
        )

@dp.message_handler(regexp=r'/change')
async def change_phone(message: Message):
    """ Смена номера. """
    chat_id = message.from_user.id
    text = message.text.split()[1]
    phone = re.findall('\d+', text)[0]
    db_change_phone(chat_id, phone)

    message_id = message.message_id
    await bot.delete_message(
        chat_id=chat_id,
        message_id=message_id   
    )
    await bot.send_message(
        chat_id=chat_id,
        text="Номер был успешно изменен!"
    )
    await show_main_menu(message)



async def start_questions(message: Message):
    await Questions.product_category.set()
    await message.answer('Добавить продукт в категорию', reply_markup=generate_admin_menu())


@dp.callback_query_handler(lambda call: 'add_categories_' in call.data, state=Questions.product_category) 
async def admin_add_products(call: CallbackQuery, state: FSMContext): 
    """ Получение названия категории в админке. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    category_id = int(call.data.split('_')[-1])
    product_category = db_get_category_by_category_id(category_id)[0]
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(
        chat_id,
        f"Вы выбрали категорию: <b>{product_category}</b>, введите название нового продукта:"
    )

    async with state.proxy() as data:
        data['product_category'] = category_id

    await Questions.next()


@dp.message_handler(content_types=['text'], state=Questions.product_name)
async def confirm_product_name(message: Message, state: FSMContext):
    """ Получение названия продукта в админке. """
    chat_id = message.chat.id
    message_id = message.message_id
    async with state.proxy() as data:
        data['product_name'] = message.text

    await bot.delete_message(chat_id, message_id)
    await message.answer(f"Название продукта: <b>{message.text}</b>, введите цену продукта:")
    await Questions.next()


@dp.message_handler(content_types=['text'], state=Questions.product_price)
async def confirm_product_price(message: Message, state: FSMContext):
    """ Получение стоимости продукта в админке. """
    async with state.proxy() as data:
        data['product_price'] = message.text

    await message.answer(f"Стоимость продукта: <b>{message.text}</b>, введите описания продукта:")
    await Questions.next()


@dp.message_handler(content_types=['text'], state=Questions.product_info)
async def confirm_product_info(message: Message, state: FSMContext):
    """ Получение описания продукта в админке. """
    async with state.proxy() as data:
        data['product_info'] = message.text
    await message.answer(f"Описание продукта: <b>{message.text}</b>, отправьте картинку продукта")
    await Questions.next()


@dp.message_handler(content_types=['photo'], state=Questions.product_photo)
async def confirm_product_photo(message: Message, state: FSMContext):
    """ Получение фото продукта в админке. """
    chat_id = message.from_user.id
    message_id = message.message_id
    await bot.delete_message(chat_id, message_id)
    async with state.proxy() as data:
        product_name = data['product_name']
        product_price = data['product_price']
        product_info = data['product_info']
        path = f'media/{product_name}.jpg'
        data['product_photo'] = path

    await message.photo[-1].download(destination_file=path)
    photo = open(path, 'rb')
    await message.answer_photo(
        photo=photo,
        caption=f'Наименования: {product_name}\n\nОписания: {product_info}\nЦена: {product_price}',
        reply_markup=add_product_ack()
    )
    await Questions.next()


@dp.callback_query_handler(lambda call: 'action' in call.data, state=Questions.product_ack)
async def add_product_finish(call: CallbackQuery, state: FSMContext):
    """ Итоговое добавление продукта в админке. """
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    action = call.data.split('_')[-1]
    await bot.delete_message(chat_id, message_id)

    async with state.proxy() as data:
        product_category = int(data['product_category'])
        product_name = data['product_name']
        product_price = int(data['product_price'])
        product_info = data['product_info']
        product_photo = data['product_photo']

    if action == 'accept':
        db_add_product_to_database(
            product_category,
            product_name,
            product_price,
            product_info,
            product_photo
        )

    await state.finish()
    await bot.send_message(chat_id, "Выход из режима администратора", reply_markup=generate_main_menu())

executor.start_polling(dp)
