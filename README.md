# 🎨 Mi AI Service - RunPod Edition

**🚀 НАСТРОИЛ РАЗ - РАБОТАЕТ НАВСЕГДА!**

## 🎯 Что это?

Полностью автоматизированный AI сервис для генерации изображений:
- 🖼️ **Stable Diffusion 3.5** + **Arabic LoRA** модели
- ☁️ **RunPod GPU** для быстрой генерации
- 🗄️ **Supabase** для хранения пользователей и изображений  
- 🔄 **Git Sync** для автоматических обновлений
- 🎨 **5 Arabic стилей**: архитектура, золото, узоры, каллиграфия, Рамадан

## ⚡ Быстрый старт

### 1️⃣ Клонирование в RunPod
```bash
# В RunPod SSH терминале:
cd /workspace
git clone https://github.com/yourusername/mi-ai-service-runpod.git
cd mi-ai-service-runpod
```

### 2️⃣ Быстрая настройка
```bash
# Автоматическая установка и запуск:
chmod +x scripts/quick-setup.sh
./scripts/quick-setup.sh
```

### 3️⃣ Результат
- ✅ **AI сервис запущен** на порту 8000
- ✅ **Автосинхронизация** каждые 5 минут
- ✅ **Автобэкап** каждый час  
- ✅ **Supabase интеграция** настроена

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │────│   Mi AI Service  │────│   Stable        │
│   Frontend      │    │   (FastAPI)      │    │   Diffusion     │
│                 │    │   Port: 8000     │    │   + Arabic LoRA │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Supabase      │    │   GitHub Repo    │    │   RunPod GPU    │
│   Database +    │    │   Auto Sync +    │    │   Cloud         │
│   Storage       │    │   Backup         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎨 Поддерживаемые стили

### 🕌 Arabic Architecture
Мечети, арки, традиционная исламская архитектура
- **Цвета**: Золотой, коричневый, бежевый
- **Промпт**: Автоматически добавляет "Islamic architecture, geometric patterns"

### ⭐ Golden Ornaments  
Золотые орнаменты, роскошные детали
- **Цвета**: Золотой, оранжевый, желтый
- **Промпт**: Добавляет "golden ornaments, luxury Arabic design"

### 🎨 Geometric Patterns
Сложные геометрические узоры
- **Цвета**: Фиолетовый, синий, изумрудный  
- **Промпт**: "Islamic geometric patterns, arabesque"

### ✍️ Arabic Calligraphy
Арабская каллиграфия и текст
- **Цвета**: Коричневый, золотой, черный
- **Промпт**: "Arabic calligraphy, Islamic art"

### 🌙 Ramadan Special
Специальные Рамадан мотивы
- **Цвета**: Пурпурный, золотой, темно-синий
- **Промпт**: "Ramadan decorations, crescent moon, lanterns"

## 🔄 Git Sync функции

### Автоматическая синхронизация
- **⏱️ Каждые 5 минут** - проверка обновлений в GitHub
- **🔄 Автообновление** кода при изменениях
- **🔃 Перезапуск сервиса** при обновлении Python файлов

### Автоматический backup
- **💾 Каждый час** - backup задач в GitHub
- **🖼️ Backup изображений** (последние 10 лучших)
- **⚙️ Backup конфигураций** с версионированием

### Удаленная разработка
- **💻 Локальная разработка** → автообновление в RunPod
- **🌐 GitHub web-интерфейс** для быстрых правок
- **📱 Мобильное редактирование** через GitHub app

## 📊 API эндпоинты

### Основные
- `POST /generate` - Генерация изображения
- `GET /task/{task_id}` - Статус генерации
- `GET /outputs/{filename}` - Скачивание изображения
- `GET /health` - Статус сервиса

### Управление
- `POST /sync` - Ручная синхронизация с GitHub
- `POST /backup` - Ручной backup
- `GET /stats` - Статистика генераций
- `POST /config/update` - Обновление конфигурации

## 🗄️ Supabase интеграция

### Таблицы базы данных
```sql
-- Пользователи (автоматически от Supabase Auth)
auth.users

-- Генерации изображений
public.generations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    task_id VARCHAR UNIQUE,
    prompt TEXT,
    style VARCHAR,
    image_url TEXT,
    thumbnail_url TEXT,
    status VARCHAR,
    rating INTEGER DEFAULT 3,
    quality_score DECIMAL,
    generation_time INTEGER,
    cost INTEGER DEFAULT 3,
    model VARCHAR DEFAULT 'Stable Diffusion 3.5',
    width INTEGER DEFAULT 1024,
    height INTEGER DEFAULT 1024,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
)
```

### Storage bucket
```
generated-images/
├── {user_id}/
│   ├── {task_id}.png      # Полное изображение
│   └── {task_id}_thumb.png # Превью
```

### Row Level Security (RLS)
- ✅ Пользователи видят только свои изображения
- ✅ Demo пользователь (UUID: 00000000-0000-0000-0000-000000000000)
- ✅ Админы видят все генерации

## 🚀 Производительность

### Оптимизации
- **⚡ Быстрая генерация** с Stable Diffusion 3.5 Large
- **🖼️ Сжатие изображений** для быстрой загрузки
- **📱 Thumbnail генерация** для превью
- **🗄️ Кеширование** частых запросов

### Мониторинг
- **📊 Логирование** всех операций
- **⏱️ Время генерации** для каждого изображения  
- **💾 Использование памяти** и GPU
- **📈 Статистика пользователей**

## 🛠️ Конфигурация

### Переменные окружения (.env)
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# GitHub (для приватных репозиториев)
GITHUB_TOKEN=your_github_token

# AI Model настройки
MODEL_NAME=stabilityai/stable-diffusion-3.5-large
ARABIC_LORA_PATH=arabic-lora-v2
GPU_MEMORY_LIMIT=8GB
```

### config.json настройки
```json
{
  "version": "2.0.0",
  "sync_interval": 300,
  "backup_interval": 3600,
  "max_image_size": 1024,
  "quality_presets": {
    "fast": {"steps": 20, "cfg": 7.0},
    "quality": {"steps": 30, "cfg": 8.0},
    "premium": {"steps": 50, "cfg": 9.0}
  }
}
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 🔴 Сервис не запускается
```bash
# Проверка логов
tail -f logs/service.log

# Перезапуск
./scripts/restart.sh
```

#### 🔴 Git sync не работает  
```bash
# Проверка Git статуса
git status
git remote -v

# Ручная синхронизация
./scripts/sync.sh
```

#### 🔴 Изображения не генерируются
```bash
# Проверка GPU
nvidia-smi

# Тест генерации
curl -X POST localhost:8000/test-generate
```

#### 🔴 Supabase ошибки
```bash
# Проверка подключения
curl -H "apikey: YOUR_KEY" YOUR_SUPABASE_URL/rest/v1/generations
```

## 📞 Поддержка

### Логи
- `logs/service.log` - Основные логи AI сервиса
- `logs/sync.log` - Логи Git синхронизации  
- `logs/backup.log` - Логи backup операций
- `logs/error.log` - Ошибки и исключения

### Команды диагностики
```bash
# Полная диагностика
./scripts/diagnose.sh

# Проверка статуса
curl localhost:8000/health

# Просмотр активных задач
curl localhost:8000/tasks/active
```

---

## 🎉 Результат

После настройки вы получите:
- ✅ **Полностью автоматический** AI сервис генерации
- ✅ **Стабильную работу** без ручных настроек  
- ✅ **Автобэкап** всех данных в GitHub
- ✅ **Быструю разработку** с Git sync
- ✅ **Масштабируемость** с Supabase
- ✅ **Мониторинг** и логирование

**🚀 НАСТРОИЛ РАЗ - РАБОТАЕТ НАВСЕГДА!** ⚡
