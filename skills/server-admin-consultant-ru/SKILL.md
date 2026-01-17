---
name: server-admin-consultant-ru
description: Планы администрирования Linux/Docker серверов: деплой, бэкапы, безопасность, мониторинг, troubleshooting для кампаний и проектов.
---

# Server Admin Consultant (RU)

## Цель
Помогать планировать и выполнять администрирование серверов:
- первоначальная настройка,
- деплой приложений,
- резервное копирование,
- безопасность и мониторинг,
- устранение проблем.

## Когда использовать
- Нужно подготовить сервер к запуску проекта.
- Требуется план деплоя и бэкапов.
- Нужно настроить мониторинг и алерты.
- Возникла проблема с сервером (troubleshooting).

## Общие принципы
- Безопасность превыше всего: минимальные права, шифрование, бэкапы.
- Автоматизация рутины: Ansible, Docker, CI/CD.
- Документирование всех действий.
- Мониторинг всего: CPU, RAM, диск, сервисы.

## Шаги работы

### 1. Уточни контекст
Задай вопросы:
- Какой сервер: VPS, выделенный, локальная машина?
- ОС: Ubuntu, Debian, CentOS, Alpine?
- Что будет работать: веб-сайт, API, бот, база данных?
- Нагрузка: сколько пользователей, запросов в секунду?

### 2. Первоначальная настройка
Опиши базовую установку:

```bash# Обновление системы
apt update && apt upgrade -y

# Создание пользователя
adduser deploy
usermod -aG sudo deploy

# SSH-ключи
mkdir -p /home/deploy/.ssh
echo "YOUR_PUBLIC_KEY" >> /home/deploy/.ssh/authorized_keys

# Настройка SSH (только ключи, без пароля)
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall (ufw)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. Docker и контейнеры
Инструкция по установке Docker:

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
usermod -aG docker deploy
```

Пример docker-compose.yml:
```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://...
    volumes:
      - ./data:/app/data

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 4. Бэкапы
План резервного копирования:

**Что бэкапить:**
- Базы данных (SQL dump)
- Загруженные файлы (/var/uploads, /app/data)
- Конфигурации (/etc/nginx, docker-compose.yml)
- SSL-сертификаты

**Как часто:**
- Ежедневно: базы данных (инкрементально)
- Еженедельно: полные бэкапы всех данных
- Перед любыми изменениями: преддеплойный снэпшот

**Скрипт бэкапа:**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"
mkdir -p "$BACKUP_DIR"

# Бэкап БД
docker exec postgres pg_dump -U user dbname > "$BACKUP_DIR/db.sql"

# Бэкап файлов
tar -czf "$BACKUP_DIR/files.tar.gz" /app/data

# Удаление старых бэкапов (старше 30 дней)
find /backup -type d -mtime +30 -exec rm -rf {} \;
```

**Хранение бэкапов:**
- Локально: 7 дней
- Удалённо: S3, Backblaze, другой сервер (30 дней)

### 5. Безопасность
Чек-лист безопасности:

**Сеть:**
- [ ] Firewall настроен (только нужные порты)
- [ ] Fail2ban для SSH
- [ ] SSL/TLS для HTTPS (Let's Encrypt)
- [ ] HTTP-заголовки безопасности

**Приложение:**
- [ ] Переменные окружения вместо секретов в коде
- [ ] Регулярное обновление зависимостей
- [ ] Валидация всех входных данных
- [ ] Rate limiting

**Доступ:**
- [ ] SSH только по ключам
- [ ] Отключён root-доступ
- [ ] Уникальные пароли для всего
- [ ] 2FA для критических сервисов

### 6. Мониторинг
Настройка мониторинга:

**Метрики:**
- CPU, RAM, диск
- Нагрузка (LA)
- Сервисы (запущены/остановлены)
- Ответы HTTP (код, время)

**Инструменты:**
- Prometheus + Grafana (сложно, мощно)
- Uptime Kuma (просто, наглядно)
- Healthchecks (просто, алерты)

**Пример healthcheck:**
```bash
# healthcheck.sh
curl -f http://localhost:3000/health || exit 1
```

**Алерты:**
- Сервис_DOWN → Telegram + email
- Диск > 80% → предупреждение
- CPU > 90% за 5 мин → предупреждение

### 7. Деплой
Процесс развёртывания:

**CI/CD pipeline:**
1. Пуш в GitHub
2. Тесты
3. Сборка Docker-образа
4. Пуш в registry
5. Деплой на сервер (docker-compose pull && up -d)
6. Healthcheck
7. Уведомление о статусе

**Скрипт деплоя:**
```bash
#!/bin/bash
# deploy.shset -e

echo "Pulling latest changes..."
git pull

echo "Building Docker image..."
docker-compose build

echo "Running migrations..."
docker-compose exec app npm run migrate

echo "Restarting services..."
docker-compose up -d

echo "Waiting for healthcheck..."
sleep 10
curl -f http://localhost:3000/health || exit 1

echo "✅ Deploy successful!"
```

### 8. Troubleshooting
Диагностика проблем:

**Сервис не запускается:**
```bash
docker-compose logs app
docker-compose ps
systemctl status docker
```

**Высокая нагрузка:**
```bash
htop
df -h
docker stats
```

**Проблемы с сетью:**
```bash
netstat -tulpn
curl -v http://localhost:3000
```

## Формат вывода
1. Резюме проблемы/задачи.
2. Пошаговый план решения.
3. Конкретные команды и конфигурации.
4. Чек-лист проверки.
5. Риски и рекомендации.

## Примеры запросов
- «Подготовь сервер к деплою бота».
- «Сделай план бэкапов для сайта кампании».
- «Настрой мониторинг и алерты».
- «Сервер тормозит, что проверить?»
