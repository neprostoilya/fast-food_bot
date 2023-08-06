from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import update, delete, select, insert
from sqlalchemy.sql.functions import sum
from sqlalchemy.exc import IntegrityError

from model import *

with Session(engine) as session:
    db_session = session


def db_check_user(telegram_id: int) -> Users | None:
    """ Проверка на существование юзера. """
    query = select(
        Users
    ).filter(
        Users.telegram_id == telegram_id
    )
    result: Users | None = db_session.scalar(query)
    return result

def db_first_register_user(full_name: str, telegram_id: int ) -> None:
    """ Первая регистрация юзера. """
    query = Users(
        full_name = full_name,
        telegram_id = telegram_id
    )
    db_session.add(query)
    db_session.commit()

def db_finally_register_user(telegram_id: int, phone: str) -> None:
    """ Финальная регистрация юзера. """
    query = update(
        Users
    ).filter(
        Users.telegram_id == telegram_id
    ).values(
        phone=phone
    )
    db_session.execute(query)
    db_session.commit()

def db_get_phone_user(telegram_id: int) -> Users:
    """ Получение номера юзера по telegram_id. """
    query = select(
        Users.phone
    ).filter(
        Users.telegram_id == telegram_id    
    )
    return db_session.scalar(query)

    
def db_create_user_cart(telegram_id: int) -> None:
    """ Создание корзинки юзера. """
    subquery = db_session.scalar(select(
        Users
    ).filter(
        Users.telegram_id == telegram_id)
    )
    query = Carts(user_id=subquery.user_id)
    db_session.add(query)
    db_session.commit()

def db_get_categories() -> Iterable:
    """ Получение категорий. """
    return db_session.scalars(select(Categories))
       
def db_get_user_cart(chat_id: int) -> Carts:
    """ Получение корзинки юзера. """
    query = select(
        Carts
    ).join(
        Users
    ).where(
        Users.telegram_id == chat_id
    )
    return db_session.scalar(query)    

def db_get_products(category_id: int) -> Iterable:
    """ Получение продуктов. """
    query = select(
        Products
    ).filter(
        Products.category_id == category_id
    )
    return db_session.scalars(query)

def db_get_product(product_id: int) -> Products:
    """ Получение информации о продукте по pk. """
    query = select(
        Products
    ).filter(
        Products.product_id == product_id
    )
    return db_session.scalar(query)

def db_get_product_by_name(product_name: str) -> Products:
    """ Получение информации о продукте по имени. """    
    query = select(
        Products
    ).filter(
        Products.product_name == product_name
    )
    return db_session.scalar(query)

def db_update_to_cart(price: DECIMAL, quantity: int, cart_id: int) -> None:
    """ Обновление сообщения. """
    if quantity:
        quantity == 1
    else: pass
    total_price = price * quantity
    query = update(
        Carts
    ).where(
        Carts.cart_id == cart_id
    ).values(
        total_price=total_price,
        total_products=quantity
    )
    db_session.execute(query)
    db_session.commit()

def db_get_final_price(telegram_id: int) -> DECIMAL:
    """ Получение финальной суммы. """
    query = select(
        sum(FinallyCarts.finall_price)
    ).join(
        Carts
    ).join(
        Users
    ).where(
        Users.telegram_id == telegram_id
    )
    return db_session.scalar(query)

def db_insert_or_update(cart_id: int, product_name: str,
        total_products: int, total_price: DECIMAL) -> bool:
    """ Добавление или изменение заказа. """
    try:
        query = insert(
            FinallyCarts
        ).values(
            cart_id=cart_id,
            product_name=product_name,
            quantity=total_products,
            finall_price=total_price
        )
        db_session.execute(query)
        db_session.commit()
        return True
    
    except IntegrityError:
        db_session.rollback()
        query = update(
            FinallyCarts
        ).where(
            FinallyCarts.product_name == product_name
        ).where(
            FinallyCarts.cart_id == cart_id
        ).values(
            quantity=total_products,
            finall_price=total_price
        )
        db_session.execute(query)
        db_session.commit()

        return False
        
def db_get_cart_products(telegram_id: int) -> Iterable:
    """ Получение информации о продукте в корзинке. """
    query = select(
        FinallyCarts.cart_id,
        FinallyCarts.product_name,
        FinallyCarts.quantity,
        FinallyCarts.finall_price
    ).join(
        Carts
    ).join(
        Users
    ).where(
        Users.telegram_id == telegram_id
    )
    return db_session.execute(query).fetchall()

def db_product_for_delete(chat_id: int) -> Iterable:
    """ Получение продукта в финальной корзинке. """
    query = select(
        FinallyCarts.finally_id,
        FinallyCarts.product_name,
    ).join(
        Carts
    ).join(
        Users
    ).where(
        Users.telegram_id == chat_id
    )
    return db_session.execute(query).fetchall()

def db_delete_product(finally_id: int) -> None:
    """ Удаление продукта из корзинки по pk. """
    query = delete(
        FinallyCarts
    ).where(
        FinallyCarts.finally_id == finally_id
    )
    db_session.execute(query)
    db_session.commit()

def db_insert_history_products(text: str, telegram_id: int):
    """ Добавление истории покупки. """
    query = insert(History
    ).values(
        telegram_id = telegram_id,
        text = text
    )
    db_session.execute(query)
    db_session.commit()
    
def db_get_history_products(telegram_id: int) -> Iterable:
    """ Получение истории покупок. """
    query = select(
        History.text
    ).filter(
        History.telegram_id == telegram_id
    ).order_by(
        History.history_id.desc()
    ).limit(
        1
    )
    return db_session.execute(query).fetchall()


def db_clear_finally_cart(cart_id: int) -> None:
    """ Очистка продуктов в финальной корзинке. """
    query = delete(
        FinallyCarts
    ).where(
        FinallyCarts.cart_id == cart_id
    )
    db_session.execute(query)
    db_session.commit()

def db_change_phone(telegram_id: int, phone: int) -> None:
    """ Изменение номера юзера. """
    query = update(
        Users
    ).filter(
        Users.telegram_id == telegram_id
    ).values(
        phone = phone
    )
    db_session.execute(query)
    db_session.commit()

def db_add_product_to_database(category: str, name: str,
    price: int, info: str, photo: bytes) -> None:
    """ Добавление продукта или категории в базу данных. """
    query = insert(
        Products
    ).values(
        category_id = category,
        product_name = name,
        product_price = price,
        description = info,
        image = photo
    )
    db_session.execute(query)
    db_session.commit()

def db_get_category_by_category_id(category_id: int) -> str:
    """ Получение название категории по pk. """
    query = select(
        Categories.category_name
    ).filter(
        Categories.category_id == category_id
    ).limit(1)
    return db_session.execute(query).fetchone()