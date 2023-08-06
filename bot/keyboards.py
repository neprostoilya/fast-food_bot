from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardButton, InlineKeyboardMarkup

from utils import *

def generate_phone_button() -> dict:
    """ Кнопка отправки контакта. """
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(text="📞 Отправить контакт", request_contact=True)]
        ], resize_keyboard=True
    )

def generate_main_menu() -> dict:
    """ Главное меню. """
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(text='✔️ Сделать заказ')],
            [KeyboardButton(text='📙 История'), 
             KeyboardButton(text='🛒 Корзинка'), 
             KeyboardButton(text='🛠️ Настройки')]
        ], resize_keyboard=True
    )

def back_to_main_menu() -> dict:
    """ Кнопка возвращения назад в главное меню. """
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='Главное меню')]
    ], resize_keyboard=True)

def generate_category_menu(chat_id: int) -> dict:
    """ Кнопка корзинки и кнопки категорий. """
    total_price = db_get_final_price(chat_id)
    categories = db_get_categories()
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton(
            text=f'Ваша корзинка  ({total_price if total_price else 0} сум)',
            callback_data='cart'
        )
    )
    buttons = []
    for category in categories:
        bnt = InlineKeyboardButton(
            text=category.category_name,
            callback_data=f"category_{category.category_id}"
        )
        buttons.append(bnt)
    markup.add(*buttons)
    return markup


def generate_products_by_category(category_id: int) -> dict:
    """ Кнопки продуктов и кнопка назад. """
    markup = InlineKeyboardMarkup(row_width=2)
    products = db_get_products(category_id)
    buttons = []
    for product in products:
        btn = InlineKeyboardButton(text=product.product_name, callback_data=f"product_{product.product_id}")
        buttons.append(btn)
    markup.add(*buttons)
    markup.row(
    InlineKeyboardButton(text='⬅ Назад', callback_data='Назад')
    )
    return markup

def generate_product_price(quantity: int) -> dict:
    """ Кнопки добавления продукта в корзинку. """
    markup = InlineKeyboardMarkup(row_width=3)
    number = quantity
    buttons = [
        InlineKeyboardButton(text='➖', callback_data='action -'),
        InlineKeyboardButton(text=f'{number}', callback_data=f'{number}'),
        InlineKeyboardButton(text='➕', callback_data='action +'),
        InlineKeyboardButton(text='Положить в корзину 😋', callback_data='put_into_cart')
    ]
    markup.add(*buttons)
    return markup

def back_to_menu() -> dict:
    """ Кнопка возвращения назад. """
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='⬅ Назад')]
    ], resize_keyboard=True)

def generate_cart_button(chat_id: int) -> InlineKeyboardMarkup:
    """ Кнопка покупки и удаления продуктов. """
    markup = InlineKeyboardMarkup(row_width=3)
    markup.row(
        InlineKeyboardButton(
            text="✅ Оформить заказ",
            callback_data=f"order"
        )
    )
    cart_products = db_product_for_delete(chat_id)
    for finally_id, name in cart_products:
        markup.row(
            InlineKeyboardButton(
                text=f"❌ {name}",
                callback_data=f"delete_{finally_id}"
            )
        )
    return markup

def generate_setings_button() -> dict:
    """ Кнопки настроек. """
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            text='Сменить номер',
            callback_data="change_phone"
        )
    )
    markup.row(
        InlineKeyboardButton(
            text="Админ панель", 
            callback_data="admin_button"
        )
    )
    return markup


def generate_admin_menu() -> dict:
    """ Кнопки выбора категорий в админке. """
    markup = InlineKeyboardMarkup(row_width=2)
    categories = db_get_categories()
    
    buttons = []
    for category in categories:
        bnt = InlineKeyboardButton(
            text=category.category_name,
            callback_data=f"add_categories_{category.category_id}"
        )
        buttons.append(bnt)
    markup.add(*buttons)
    return markup


def add_product_ack() -> dict:
    """ Кнопки добавления или удаления продукта. """
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text='✔', callback_data='action_accept'),
        InlineKeyboardButton(text='❌', callback_data='action_drop')
    ]
    markup.add(*buttons)
    return markup

