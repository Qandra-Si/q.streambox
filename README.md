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

Либо запустить в `screen` команды (выйти с помощью `Ctrl+A+D`):

```bash
.venv/bin/python3 load.py
.venv/bin/python3 load_alliance.py
```

Либо создать systemd service(s):

```bash
# скопируй и настрой q_streambox.service
cp q_streambox.service.template q_streambox.service
# впиши имя пользователя и путь к директории с программой
nano q_streambox.service
# установка и запуск сервиса
sudo mv -fv q_streambox.service /lib/systemd/system/q_streambox.service
sudo chmod 644 /lib/systemd/system/q_streambox.service
sudo systemctl --system daemon-reload
sudo systemctl restart q_streambox.service
# см. лог работы
sudo journalctl -f -u q_streambox

# скопируй и настрой q_streambox_alliance.service
cp q_streambox_alliance.service.template q_streambox_alliance.service
# впиши имя пользователя и путь к директории с программой
nano q_streambox_alliance.service
# установка и запуск сервиса
sudo mv -fv q_streambox_alliance.service /lib/systemd/system/q_streambox_alliance.service
sudo chmod 644 /lib/systemd/system/q_streambox_alliance.service
sudo systemctl --system daemon-reload
sudo systemctl restart q_streambox_alliance.service
# см. лог работы
sudo journalctl -f -u q_streambox_alliance
```

