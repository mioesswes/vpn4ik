# Что нужно от вас для полного запуска

## 1. Доступы Telegram

- `BOT_TOKEN`
- список `ADMIN_IDS`
- при желании отдельный `SUPPORT_CHAT_ID`

## 2. База и Redis

- `DATABASE_URL`
- `REDIS_URL`

## 3. По каждой VPN-ноде

Для `Germany`, `Sweden`, `Finland`, `USA`:

- публичный домен или IP для клиента
- клиентский порт
- `Reality public key`
- `Reality short id`
- `Reality server name / SNI`

## 4. Для реальной 3x-ui интеграции

Если хотите не только генерировать конфиг, но и ходить в панель:

- `PANEL_URL`
- `PANEL_USERNAME`
- `PANEL_PASSWORD`
- `INBOUND_ID`

## 5. Для платежки позже

Сейчас backend уже умеет:

- создавать top-up request
- хранить сумму и срок
- хранить статус

Когда появится платежный провайдер, останется:

- создать invoice / payment link
- сохранить `external_payment_id`
- по webhook или polling перевести запрос в `paid`
- продлить подписку пользователю
