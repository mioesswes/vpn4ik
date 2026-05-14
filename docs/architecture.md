# Архитектура Telegram VPN Service

## 1. Контур системы

### Main Server

- Telegram Bot на `aiogram 3`
- PostgreSQL для пользователей, подписок, платежей, тикетов, нод
- Redis для rate limit, FSM, временных ключей, anti-spam
- Internal API на `FastAPI`
- APScheduler для фоновых задач
- Monitoring layer для сбора статусов нод и алертов админу

### VPN Nodes

4 отдельные ноды:

- Germany
- Sweden
- Finland
- USA

Каждая нода:

- Ubuntu 22.04
- Xray-core
- Reality inbound
- единый system UUID
- доступ через 3x-ui API

## 2. Слои в репозитории

### `/bot`

Отвечает за пользовательский Telegram UX:

- главное меню
- раздел конфигов
- профиль
- продление
- поддержка

### `/admin`

Inline-админка в Telegram:

- статистика
- управление серверами
- управление пользователями
- тикеты
- рассылки

### `/payments`

Платежная логика:

- создание invoice
- маппинг тарифа в длительность подписки
- активация подписки после подтверждения оплаты

### `/support`

Тикеты и ответы поддержки:

- создание обращения
- генерация `ticket_id`
- уведомление администратора
- отправка reply-ответа пользователю

### `/xray`

Интеграция с VPN слоем:

- выдача VLESS Reality конфига
- смена активной локации
- сброс конфига
- получение данных по online users / traffic

### `/monitoring`

Проверка нод и алертинг:

- offline
- high load
- xray stopped
- packet loss

### `/database`

Сущности и доступ к данным:

- users
- payments
- support_tickets
- vpn_nodes

## 3. Основные доменные сущности

### User

- `telegram_id`
- `username`
- `subscription_status`
- `subscription_expires_at`
- `active_location`
- `traffic_used_bytes`
- `device_limit`
- `is_banned`

### Payment

- `provider`
- `status`
- `amount_rub`
- `duration_months`
- `external_payment_id`

### SupportTicket

- `ticket_code`
- `status`
- `message_text`
- `admin_reply_text`

### VpnNode

- `location`
- `hostname`
- `panel_url`
- `xray_inbound_id`
- `is_enabled`

## 4. MVP поток

### 1. Выдача VPN

1. Пользователь открывает `Конфиг`
2. Бот берет текущую `active_location`
3. Сервис `/xray` собирает VLESS Reality конфиг
4. Бот отдает текст конфига и QR

### 2. Смена локации

1. Пользователь нажимает `Сменить локацию`
2. Выбирает Germany / Sweden / Finland / USA
3. Обновляется `active_location`
4. Генерируется новый конфиг

### 3. Продление

1. Пользователь выбирает тариф
2. Выбирает провайдера оплаты
3. Создается invoice
4. После подтверждения продлевается `subscription_expires_at`

### 4. Поддержка

1. Пользователь создает обращение
2. Система сохраняет тикет
3. Админ получает уведомление
4. Админ отвечает reply-сообщением
5. Пользователь получает ответ

## 5. Безопасность

- Redis rate-limit на входящие Telegram updates
- anti-spam по частоте команд и созданию тикетов
- device limit на пользователя
- audit log для админских действий
- auto-ban abuse users
- алерты по нестабильным нодам

## 6. Следующий шаг по реализации

1. Добавить слой репозиториев и миграции Alembic
2. Поднять FSM сценарии для пользователя и админа
3. Реализовать 3x-ui client
4. Подключить webhook/polling для платежей
5. Привязать Redis middleware для rate limiting
6. Добавить реальные health checks нод
