# q.streambox

Настройка стримбоксов:

Blood Khanid:
 * http://194.34.238.193:8084/
 * https://zkillboard.com/character/1904811443/streambox/

The Crimson Feed:
 * http://194.34.238.193:8085/
 * https://zkillboard.com/alliance/99014727/streambox/

Оригинальный отображает на интервале 8 часов, мой на интервале 12 часов + добавляет стили.

Установка:

```bash
sudo apt install python3 python3-venv

python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Отредактировать файл `/etc/nginx/sites-available/zkb`:

```txt
server {
    listen 194.34.238.193:8084;
    server_name  rindustry.ru;

    location / {
        proxy_pass http://127.0.0.1:8084;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
server {
    listen 194.34.238.193:8085;
    server_name  rindustry.ru;

    location / {
        proxy_pass http://127.0.0.1:8085;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Создать ссылку:


```bash
sudo ln -s /etc/nginx/sites-available/zkb /etc/nginx/sites-enabled/
```

Проверить и перезапустить nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

Запустить в `screen` команду (выйти с помощью `Ctrl+A+D`):

```bash
.venv/bin/python3 load.py
```

Запустить в `screen` ещё одну команду (выйти с помощью `Ctrl+A+D`):

```bash
.venv/bin/python3 load_alliance.py
```

