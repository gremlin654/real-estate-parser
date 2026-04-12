"""
Обработчики подписок Telegram бота.

Реализует FSM wizard для создания/редактирования подписок:
/subscribe → город → комнаты → цена min → цена max → подтверждение

Также обработчики для /settings, /unsubscribe и управления подписками.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import CITY_NAMES
from app.services.telegram_subscription_service import TelegramSubscriptionService
from app.services.telegram_exceptions import (
    SubscriptionLimitExceeded,
    UserNotFoundError,
)
from app.telegram.keyboards.inline import (
    get_city_keyboard,
    get_rooms_keyboard,
    get_subscription_confirmation_keyboard,
    get_subscriptions_list_keyboard,
    get_edit_subscription_keyboard,
    get_price_input_keyboard,
    CityCallback,
    RoomsCallback,
    SubscriptionActionCallback,
    EditSubscriptionCallback,
    EditSubscriptionFieldCallback,
    DeleteSubscriptionCallback,
)
from app.telegram.keyboards.reply import (
    get_main_keyboard,
    get_cancel_keyboard,
)

router = Router()


# === FSM States ===


class SubscriptionStates(StatesGroup):
    """Состояния FSM для wizard создания/редактирования подписки."""

    waiting_for_city = State()
    waiting_for_rooms = State()
    waiting_for_price_min = State()
    waiting_for_price_max = State()
    waiting_for_confirmation = State()
    editing_subscription = State()


# === Команда /subscribe ===


@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, state: FSMContext):
    """
    Начать создание подписки — показать выбор города.

    Сбрасывает предыдущее состояние FSM и запускает wizard.
    """
    logger.info(f"User {message.from_user.id} started /subscribe flow")

    # Очищаем предыдущее состояние
    await state.clear()

    # Устанавливаем первое состояние
    await state.set_state(SubscriptionStates.waiting_for_city)

    await message.answer(
        "🏙️ <b>Выберите город для мониторинга:</b>",
        reply_markup=get_city_keyboard(),
    )


# === Выбор города ===


@router.callback_query(SubscriptionStates.waiting_for_city, CityCallback.filter())
async def process_city_selection(
    callback: types.CallbackQuery,
    callback_data: CityCallback,
    state: FSMContext,
):
    """
    Обработать выбор города.

    Сохраняет город в FSM state и переходит к выбору комнат.
    """
    city = callback_data.city
    city_name = CITY_NAMES.get(city, city)

    logger.info(f"User {callback.from_user.id} selected city: {city}")

    # Сохраняем город
    await state.update_data(city=city)

    # Переходим к следующему состоянию
    await state.set_state(SubscriptionStates.waiting_for_rooms)

    await callback.message.edit_text(
        f"🚪 <b>Выберите количество комнат:</b>\n\n" f"Город: {city_name}",
        reply_markup=get_rooms_keyboard(),
    )
    await callback.answer()


# === Выбор комнат ===


@router.callback_query(SubscriptionStates.waiting_for_rooms, RoomsCallback.filter())
async def process_rooms_selection(
    callback: types.CallbackQuery,
    callback_data: RoomsCallback,
    state: FSMContext,
):
    """
    Обработать выбор комнат.

    Сохраняет комнаты в FSM state и переходит к вводу цены min.
    """
    rooms_value = callback_data.rooms

    # Обработка "Любые" комнаты
    if rooms_value == "any":
        rooms = None
        rooms_text = "Любые"
    elif rooms_value == "5":
        rooms = [5]
        rooms_text = "5+"
    else:
        rooms = [int(rooms_value)]
        rooms_text = f"{rooms_value} комн."

    logger.info(f"User {callback.from_user.id} selected rooms: {rooms}")

    # Сохраняем комнаты
    await state.update_data(rooms=rooms)

    # Получаем город для отображения
    data = await state.get_data()
    city_name = CITY_NAMES.get(data.get("city", ""), data.get("city", ""))

    # Переходим к следующему состоянию
    await state.set_state(SubscriptionStates.waiting_for_price_min)

    await callback.message.edit_text(
        f"💰 <b>Введите минимальную цену (USD):</b>\n\n"
        f"🏙️ Город: {city_name}\n"
        f"🚪 Комнаты: {rooms_text}\n\n"
        f"Отправьте число или нажмите 'Пропустить'",
        reply_markup=get_price_input_keyboard(),
    )
    await callback.answer()


# === Пропуск цены ===


@router.callback_query(lambda c: c.data == "skip_price")
async def skip_price(callback: types.CallbackQuery, state: FSMContext):
    """Пропустить ввод цены — перейти к подтверждению подписки"""
    await state.update_data(price_min=None, price_max=None)
    data = await state.get_data()
    city_name = CITY_NAMES.get(data.get("city", ""), data.get("city", ""))
    rooms_value = data.get("rooms")
    if rooms_value is None:
        rooms_text = "Любые"
    elif rooms_value == [5]:
        rooms_text = "5+"
    else:
        rooms_text = f"{rooms_value[0]} комн."

    await callback.message.edit_text(
        f"✅ <b>Подтвердите подписку:</b>\n\n"
        f"🏙️ Город: {city_name}\n"
        f"🚪 Комнаты: {rooms_text}\n"
        f"💰 Цена: Любая\n\n"
        f"Нажмите '✅ Подтвердить' для создания подписки",
        reply_markup=get_subscription_confirmation_keyboard(),
    )
    await callback.answer()


# === Подтверждение подписки ===


@router.callback_query(lambda c: c.data == "cancel_subscription")
async def cancel_subscription_callback(callback: types.CallbackQuery, state: FSMContext):
    """Отменить создание подписки (inline кнопка)"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание подписки отменено.\n\n"
        "Используйте /subscribe для начала заново.",
    )
    await callback.answer()


@router.message(SubscriptionStates.waiting_for_price_min)
async def process_price_min(message: types.Message, state: FSMContext):
    """
    Обработать ввод минимальной цены.

    Валидирует что введено число и переходит к подтверждению подписки.
    """
    # Валидируем число
    try:
        price_min = int(message.text.strip().replace(",", "").replace(" ", ""))
        if price_min <= 0:
            raise ValueError("Цена должна быть положительным числом")
    except (ValueError, AttributeError):
        await message.answer(
            "❌ <b>Неверный формат цены.</b>\n\n"
            "Отправьте целое число, например: <code>50000</code>\n\n"
            f"Или нажмите 'Пропустить' для любой цены.",
            reply_markup=get_price_input_keyboard(),
        )
        return

    logger.info(f"User {message.from_user.id} entered price_min: {price_min}")

    # Сохраняем цену
    await state.update_data(price_min=price_min)

    # Переходим к подтверждению подписки
    await _show_confirmation(message, state)


async def _proceed_to_price_max(message: types.Message, state: FSMContext):
    """Перейти к вводу максимальной цены."""
    # Получаем данные из state
    data = await state.get_data()
    city_name = CITY_NAMES.get(data.get("city", ""), data.get("city", ""))
    rooms = data.get("rooms")
    rooms_text = _format_rooms(rooms)

    price_min = data.get("price_min")
    price_min_text = f"${price_min:,}" if price_min else "Любая"

    # Переходим к следующему состоянию
    await state.set_state(SubscriptionStates.waiting_for_price_max)

    await message.answer(
        f"💰 <b>Введите максимальную цену (USD):</b>\n\n"
        f"🏙️ Город: {city_name}\n"
        f"🚪 Комнаты: {rooms_text}\n"
        f"💵 Мин. цена: {price_min_text}\n\n"
        f"Отправьте число или нажмите 'Пропустить'",
        reply_markup=get_price_input_keyboard(),
    )


# === Ввод максимальной цены ===


@router.message(SubscriptionStates.waiting_for_price_max)
async def process_price_max(message: types.Message, state: FSMContext):
    """
    Обработать ввод максимальной цены.

    Валидирует число и показывает подтверждение.
    """
    # Проверяем кнопку отмены
    if message.text == "❌ Отменить":
        await cancel_flow(message, state)
        return

    # Проверяем кнопку пропуска
    if message.text == "⏭️ Пропустить (любая цена)":
        await state.update_data(price_max=None)
        await _show_confirmation(message, state)
        return

    # Валидируем число
    try:
        price_max = int(message.text.strip().replace(",", "").replace(" ", ""))
        if price_max <= 0:
            raise ValueError("Цена должна быть положительным числом")
    except (ValueError, AttributeError):
        await message.answer(
            "❌ <b>Неверный формат цены.</b>\n\n"
            "Отправьте целое число, например: <code>150000</code>\n\n"
            f"Или нажмите 'Пропустить' для любой цены.",
            reply_markup=get_price_input_keyboard(),
        )
        return

    # Проверяем что price_max > price_min
    data = await state.get_data()
    price_min = data.get("price_min")
    if price_min and price_max <= price_min:
        await message.answer(
            f"❌ <b>Максимальная цена должна быть больше минимальной.</b>\n\n"
            f"Мин. цена: ${price_min:,}\n"
            f"Введите число больше ${price_min:,}",
            reply_markup=get_price_input_keyboard(),
        )
        return

    logger.info(f"User {message.from_user.id} entered price_max: {price_max}")

    # Сохраняем цену
    await state.update_data(price_max=price_max)

    await _show_confirmation(message, state)


# === Показ подтверждения ===


async def _show_confirmation(message: types.Message, state: FSMContext):
    """Показать сводку подписки и запросить подтверждение."""
    data = await state.get_data()

    city_name = CITY_NAMES.get(data.get("city", ""), data.get("city", ""))
    rooms_text = _format_rooms(data.get("rooms"))
    price_min = data.get("price_min")
    price_max = data.get("price_max")

    price_min_text = f"${price_min:,}" if price_min else "Любая"
    price_max_text = f"${price_max:,}" if price_max else "Любая"

    # Переходим к состоянию подтверждения
    await state.set_state(SubscriptionStates.waiting_for_confirmation)

    confirmation_text = (
        f"✅ <b>Подтвердите подписку:</b>\n\n"
        f"🏙️ Город: {city_name}\n"
        f"🚪 Комнаты: {rooms_text}\n"
        f"💰 Цена: {price_min_text} — {price_max_text}\n\n"
        f"Вы будете получать уведомления о новых квартирах\n"
        f"с такими параметрами."
    )

    await message.answer(
        confirmation_text,
        reply_markup=get_subscription_confirmation_keyboard(),
    )


# === Подтверждение подписки ===


@router.callback_query(SubscriptionActionCallback.filter())
async def confirm_subscription(
    callback: types.CallbackQuery,
    callback_data: SubscriptionActionCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """
    Создать подписку после подтверждения.
    """
    # Проверяем что это confirm а не cancel
    if callback_data.action == "confirm":
        pass  # Продолжаем обработку ниже
    elif callback_data.action == "cancel":
        await state.clear()
        await callback.message.answer("❌ Создание подписки отменено.")
        await callback.answer()
        return
    elif callback_data.action == "add_new":
        # Начать новую подписку
        await state.clear()
        await callback.message.answer(
            "🏙️ <b>Выберите город для мониторинга:</b>",
            reply_markup=get_city_keyboard(),
        )
        await state.set_state(SubscriptionStates.waiting_for_city)
        await callback.answer()
        return

    logger.info(f"User {callback.from_user.id} CONFIRMED subscription, callback_data={callback_data}")

    # Получаем данные из state
    data = await state.get_data()
    logger.info(f"FSM state data: city={data.get('city')}, rooms={data.get('rooms')}, price_min={data.get('price_min')}, price_max={data.get('price_max')}")
    city = data.get("city")
    rooms = data.get("rooms")
    price_min = data.get("price_min")
    price_max = data.get("price_max")

    try:
        # Получаем пользователя
        service = TelegramSubscriptionService(session)
        user = await service.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(
                "❌ Ошибка: вы не зарегистрированы. Используйте /start"
            )
            await state.clear()
            return

        # Создаём подписку
        subscription = await service.create_subscription(
            user_id=user.id,
            city=city,
            rooms=rooms,
            price_min=price_min,
            price_max=price_max,
            currency="usd",
        )

        # Очищаем состояние
        await state.clear()

        # Показываем результат
        city_name = CITY_NAMES.get(city, city)
        rooms_text = _format_rooms(rooms)
        price_min_text = f"${price_min:,}" if price_min else "Любая"
        price_max_text = f"${price_max:,}" if price_max else "Любая"

        success_text = (
            f"🎉 <b>Подписка создана!</b>\n\n"
            f"🏙️ Город: {city_name}\n"
            f"🚪 Комнаты: {rooms_text}\n"
            f"💰 Цена: {price_min_text} — {price_max_text}\n\n"
            f"Вы получите уведомление когда появится\n"
            f"новая квартира с такими параметрами.\n\n"
            f"Используйте /settings для управления подписками."
        )

        # Отправляем новое сообщение вместо edit_text
        await callback.message.answer(
            success_text,
            reply_markup=get_main_keyboard(),
        )
        # Скрываем сообщение подтверждения
        try:
            await callback.message.delete()
        except Exception:
            pass

        logger.info(
            f"Subscription created: id={subscription.id}, "
            f"user={user.id}, city={city}"
        )

    except SubscriptionLimitExceeded as e:
        await callback.message.edit_text(
            f"❌ <b>Превышен лимит подписок.</b>\n\n"
            f"Максимум 5 активных подписок на пользователя.\n"
            f"У вас уже {e.current_count} подписок.\n\n"
            f"Используйте /settings для удаления старых подписок."
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        await callback.message.edit_text(
            "❌ <b>Ошибка при создании подписки.</b>\n\n"
            f"Попробуйте ещё раз или обратитесь в поддержку.\n\n"
            f"Ошибка: {str(e)}"
        )
        await state.clear()

    await callback.answer()


# === Отмена создания подписки ===


@router.callback_query(
    SubscriptionStates.waiting_for_confirmation,
    SubscriptionActionCallback.filter(F.action == "cancel"),
)
async def cancel_subscription(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    """Отменить создание подписки."""
    logger.info(f"User {callback.from_user.id} cancelled subscription creation")

    await cancel_flow(callback.message, state)
    await callback.answer()


async def cancel_flow(message: types.Message, state: FSMContext):
    """
    Универсальная функция отмены wizard.

    Очищает state и возвращает главную клавиатуру.
    """
    await state.clear()

    await message.answer(
        "❌ <b>Создание подписки отменено.</b>\n\n"
        f"Используйте /subscribe для начала заново.",
        reply_markup=get_main_keyboard(),
    )

    logger.info("Subscription wizard cancelled")


# === Обработка отмены через текстовую кнопку ===


@router.message(SubscriptionStates.waiting_for_price_min, F.text == "❌ Отменить")
async def cancel_via_text_price_min(message: types.Message, state: FSMContext):
    """Обработать текстовую кнопку отмены при вводе price_min."""
    await cancel_flow(message, state)


@router.message(SubscriptionStates.waiting_for_price_max, F.text == "❌ Отменить")
async def cancel_via_text_price_max(message: types.Message, state: FSMContext):
    """Обработать текстовую кнопку отмены при вводе price_max."""
    await cancel_flow(message, state)


# === Команда /settings ===


@router.message(Command("settings"))
async def cmd_settings(message: types.Message, session: AsyncSession):
    """
    Показать текущие подписки пользователя.

    Response:
        📋 Ваши подписки (2/5):

        1️⃣ Минск | 2 комнаты | $50,000-$150,000
           [✏️ Редактировать] [🗑 Удалить]

        2️⃣ Могилёв | Любые комнаты | Любая цена
           [✏️ Редактировать] [🗑 Удалить]

        [➕ Добавить новую]
    """
    logger.info(f"User {message.from_user.id} requested /settings")

    service = TelegramSubscriptionService(session)
    user = await service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return

    # Получаем активные подписки
    subscriptions = await service.get_active_subscriptions(user.id)

    if not subscriptions:
        await message.answer(
            "📋 <b>У вас нет активных подписок.</b>\n\n"
            f"Используйте /subscribe для создания первой подписки.",
            reply_markup=get_main_keyboard(),
        )
        return

    # Формируем текст
    count = len(subscriptions)
    settings_text = f"📋 <b>Ваши подписки ({count}/5):</b>\n\n"

    for idx, sub in enumerate(subscriptions, start=1):
        city_name = CITY_NAMES.get(sub.city, sub.city)
        rooms_text = _format_rooms(sub.rooms)

        if sub.price_min and sub.price_max:
            price_text = f"${sub.price_min:,}-${sub.price_max:,}"
        elif sub.price_min:
            price_text = f"от ${sub.price_min:,}"
        elif sub.price_max:
            price_text = f"до ${sub.price_max:,}"
        else:
            price_text = "Любая"

        settings_text += f"<b>{idx}.</b> {city_name} | {rooms_text} | {price_text}\n"

    await message.answer(
        settings_text,
        reply_markup=get_subscriptions_list_keyboard(subscriptions),
    )


# === Редактирование подписки ===


@router.callback_query(EditSubscriptionCallback.filter())
async def edit_subscription(
    callback: types.CallbackQuery,
    callback_data: EditSubscriptionCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """Начать редактирование подписки с проверкой владельца."""
    subscription_id_str = callback_data.subscription_id
    user_id = callback.from_user.id

    try:
        subscription_id = UUID(subscription_id_str)
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID подписки", show_alert=True)
        return

    logger.info(f"User {user_id} editing subscription {subscription_id}")

    service = TelegramSubscriptionService(session)
    subscription = await service.get_subscription_by_id(subscription_id)

    if not subscription:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await callback.answer("❌ Это не ваша подписка", show_alert=True)
        return

    # Показываем текущие параметры и клавиатуру редактирования
    city_name = CITY_NAMES.get(subscription.city, subscription.city)
    rooms_text = _format_rooms(subscription.rooms)

    if subscription.price_min and subscription.price_max:
        price_text = f"${subscription.price_min:,}-${subscription.price_max:,}"
    elif subscription.price_min:
        price_text = f"от ${subscription.price_min:,}"
    elif subscription.price_max:
        price_text = f"до ${subscription.price_max:,}"
    else:
        price_text = "Любая"

    edit_text = (
        f"✏️ <b>Редактирование подписки:</b>\n\n"
        f"🏙️ Город: {city_name}\n"
        f"🚪 Комнаты: {rooms_text}\n"
        f"💰 Цена: {price_text}\n\n"
        f"Выберите что изменить:"
    )

    await callback.message.edit_text(
        edit_text,
        reply_markup=get_edit_subscription_keyboard(subscription_id_str),
    )
    await callback.answer()


# === Обработка выбора поля для редактирования ===


@router.callback_query(EditSubscriptionFieldCallback.filter())
async def handle_edit_field_callback(
    callback: types.CallbackQuery,
    callback_data: EditSubscriptionFieldCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """Обработать выбор поля для редактирования."""
    await _edit_subscription_field(callback, callback_data, state, session)


async def _edit_subscription_field(
    callback: types.CallbackQuery,
    callback_data: EditSubscriptionFieldCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """Обработать редактирование конкретного поля подписки с проверкой владельца."""
    subscription_id_str = callback_data.subscription_id
    field = callback_data.field
    user_id = callback.from_user.id

    try:
        subscription_id = UUID(subscription_id_str)
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID подписки", show_alert=True)
        return

    logger.info(
        f"User {user_id} editing field '{field}' "
        f"of subscription {subscription_id}"
    )

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    service = TelegramSubscriptionService(session)
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await callback.answer("❌ Это не ваша подписка", show_alert=True)
        return

    # Сохраняем информацию о редактировании в state
    await state.update_data(
        editing_subscription_id=str(subscription_id),
        editing_field=field,
    )

    await state.set_state(SubscriptionStates.editing_subscription)

    if field == "city":
        await callback.message.edit_text(
            "🏙️ <b>Выберите новый город:</b>",
            reply_markup=get_city_keyboard(),
        )
    elif field == "rooms":
        await callback.message.edit_text(
            "🚪 <b>Выберите количество комнат:</b>",
            reply_markup=get_rooms_keyboard(),
        )
    elif field == "price":
        await callback.message.edit_text(
            "💰 <b>Введите минимальную цену (USD):</b>\n\n"
            "Отправьте число или 'Пропустить'",
            reply_markup=get_price_input_keyboard(),
        )
    else:
        await callback.answer("❌ Неизвестное поле для редактирования", show_alert=True)


# === Удаление подписки ===


@router.callback_query(DeleteSubscriptionCallback.filter())
async def delete_subscription(
    callback: types.CallbackQuery,
    callback_data: DeleteSubscriptionCallback,
    session: AsyncSession,
):
    """Удалить подписку (soft delete) с проверкой владельца."""
    subscription_id_str = callback_data.subscription_id
    user_id = callback.from_user.id

    try:
        subscription_id = UUID(subscription_id_str)
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID подписки", show_alert=True)
        return

    logger.info(f"User {user_id} deleting subscription {subscription_id}")

    service = TelegramSubscriptionService(session)
    subscription = await service.get_subscription_by_id(subscription_id)

    if not subscription:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await callback.answer("❌ Это не ваша подписка", show_alert=True)
        return

    # Только теперь удалять
    success = await service.delete_subscription(subscription_id)

    if success:
        await callback.message.edit_text(
            f"🗑 <b>Подписка удалена.</b>\n\n"
            f"Вы больше не будете получать уведомления по этой подписке."
        )
        logger.info(f"Subscription {subscription_id} deleted")
    else:
        await callback.message.edit_text("❌ Ошибка: подписка не найдена")
        logger.warning(f"Failed to delete subscription {subscription_id}")

    await callback.answer()


# === Команда /unsubscribe ===


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message, session: AsyncSession):
    """
    Отписаться от всех подписок.

    Деактивирует все активные подписки пользователя.
    """
    logger.info(f"User {message.from_user.id} requested /unsubscribe")

    service = TelegramSubscriptionService(session)
    user = await service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return

    # Получаем активные подписки
    subscriptions = await service.get_active_subscriptions(user.id)

    if not subscriptions:
        await message.answer(
            "📋 <b>У вас нет активных подписок.</b>\n\n" f"Нечего отменять."
        )
        return

    # Деактивируем все подписки
    count = len(subscriptions)
    for sub in subscriptions:
        await service.delete_subscription(sub.id)

    await message.answer(
        f"🗑 <b>Все подписки удалены ({count} шт.)</b>\n\n"
        f"Вы больше не будете получать уведомления.\n\n"
        f"Используйте /subscribe для создания новых подписок.",
        reply_markup=get_main_keyboard(),
    )

    logger.info(f"User {message.from_user.id} unsubscribed from {count} subscriptions")


# === Обработка состояний редактирования ===


@router.callback_query(SubscriptionStates.editing_subscription, CityCallback.filter())
async def process_edit_city(
    callback: types.CallbackQuery,
    callback_data: CityCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """Обработать выбор города при редактировании с проверкой владельца."""
    data = await state.get_data()
    subscription_id = UUID(data["editing_subscription_id"])
    user_id = callback.from_user.id

    service = TelegramSubscriptionService(session)

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await callback.answer("❌ Это не ваша подписка", show_alert=True)
        return

    await service.update_subscription(subscription_id, city=callback_data.city)

    city_name = CITY_NAMES.get(callback_data.city, callback_data.city)
    await callback.message.edit_text(
        f"✅ Город изменён на: {city_name}",
        reply_markup=get_main_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(SubscriptionStates.editing_subscription, RoomsCallback.filter())
async def process_edit_rooms(
    callback: types.CallbackQuery,
    callback_data: RoomsCallback,
    state: FSMContext,
    session: AsyncSession,
):
    """Обработать выбор комнат при редактировании с проверкой владельца."""
    data = await state.get_data()
    subscription_id = UUID(data["editing_subscription_id"])
    user_id = callback.from_user.id

    rooms_value = callback_data.rooms
    if rooms_value == "any":
        rooms = None
    elif rooms_value == "5":
        rooms = [5]
    else:
        rooms = [int(rooms_value)]

    service = TelegramSubscriptionService(session)

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return

    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await callback.answer("❌ Это не ваша подписка", show_alert=True)
        return

    await service.update_subscription(subscription_id, rooms=rooms)

    rooms_text = _format_rooms(rooms)
    await callback.message.edit_text(
        f"✅ Комнаты изменены на: {rooms_text}",
        reply_markup=get_main_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.message(SubscriptionStates.editing_subscription)
async def process_edit_price(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    """Обработать ввод цены при редактировании с проверкой владельца."""
    if message.text == "❌ Отменить":
        await cancel_flow(message, state)
        return

    if message.text == "⏭️ Пропустить (любая цена)":
        data = await state.get_data()
        subscription_id = UUID(data["editing_subscription_id"])
        user_id = message.from_user.id

        service = TelegramSubscriptionService(session)

        # ПРОВЕРКА: подписка принадлежит текущему пользователю
        subscription = await service.get_subscription_by_id(subscription_id)
        if not subscription:
            await message.answer("❌ Подписка не найдена", reply_markup=get_main_keyboard())
            await state.clear()
            return

        user = await service.get_user_by_telegram_id(user_id)
        if not user or subscription.user_id != user.id:
            await message.answer("❌ Это не ваша подписка", reply_markup=get_main_keyboard())
            await state.clear()
            return

        await service.update_subscription(
            subscription_id, price_min=None, price_max=None
        )

        await message.answer(
            "✅ Цена изменена на: Любая",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    try:
        price = int(message.text.strip().replace(",", "").replace(" ", ""))
        if price <= 0:
            raise ValueError()
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Неверный формат. Отправьте целое число.",
            reply_markup=get_price_input_keyboard(),
        )
        return

    data = await state.get_data()
    subscription_id = UUID(data["editing_subscription_id"])
    user_id = message.from_user.id

    service = TelegramSubscriptionService(session)

    # ПРОВЕРКА: подписка принадлежит текущему пользователю
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        await message.answer("❌ Подписка не найдена", reply_markup=get_main_keyboard())
        await state.clear()
        return

    user = await service.get_user_by_telegram_id(user_id)
    if not user or subscription.user_id != user.id:
        await message.answer("❌ Это не ваша подписка", reply_markup=get_main_keyboard())
        await state.clear()
        return

    # Обновляем только price_min для простоты
    await service.update_subscription(subscription_id, price_min=price)

    await message.answer(
        f"✅ Цена изменена на: от ${price:,}",
        reply_markup=get_main_keyboard(),
    )
    await state.clear()


# === Хелперы ===


def _format_rooms(rooms: list | None) -> str:
    """
    Форматирует количество комнат для отображения.

    Args:
        rooms: Список комнат или None

    Returns:
        Строка с количеством комнат
    """
    if rooms is None or len(rooms) == 0:
        return "Любые"
    if rooms == [5]:
        return "5+ комнат"

    room_names = []
    for r in rooms:
        if r == 1:
            room_names.append("1 комната")
        elif r in (2, 3, 4):
            room_names.append(f"{r} комнаты")
        else:
            room_names.append(f"{r}+ комнат")

    return ", ".join(room_names)
