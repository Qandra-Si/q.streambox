# Author: Qandra Si
#
# pip install beautifulsoup4 lxml
import os
import json
from urllib.request import urlopen
from http.server import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup
from datetime import datetime, timezone


zkb_url = 'https://zkillboard.com'
path = '/character/1904811443/'
hours_to_show = 12
our_id = path.split('/')[2]

def load_json_from_url(url):
    try:
        with urlopen(url, timeout=20) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                print(f"Error fetching data: {response.getcode()}")
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def load_html_from_url(url):
    try:
        with urlopen(url, timeout=20) as response:
            if response.getcode() == 200:
                return response.read().decode('utf-8')
            else:
                print(f"Error fetching data: {response.getcode()}")
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

formatIskIndex = ['', 'k', 'm', 'b', 't', 'k t', 'm t', 'b t']
def formatISK(value, decimals = 1):
    value = float(value)
    if value < 10000:
        return value
    i = 0
    while value > 999.99:
        value = value / 1000
        i += 1
    return f"{value:.1f}{formatIskIndex[i]}"

obsolete_kills = []
cached_kills = {}

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        requested_path = self.path
        if requested_path != "/":
            self.send_error(404, "File Not Found")
            return

        current_utc_time = int(datetime.now(timezone.utc).timestamp())
        print(f"current_utc_time = {current_utc_time}")
        after_epoch = current_utc_time - (3600 * hours_to_show)  # show kills N hours old or less
        #print(f"after_epoch = {after_epoch}")
        #json_data = load_json_from_url(f"{zkb_url}/cache/24hour/killlist/?s=94620140&u=" + path)
        json_data = load_json_from_url(f"{zkb_url}/cache/bypass/killlist/?u=" + path)

        content = ''
        if json_data:
            content = ' '
            print(f' last kill = {json_data[0]}')
            for kill in json_data:
                kill_num: int = int(kill)
                #print(f"kill = {kill}")
                if kill_num in obsolete_kills:
                    break  # ускорение загрузки страницы

                cached = cached_kills.get(kill)
                if cached:
                    if (cached['epoch'] < after_epoch):
                        obsolete_kills.append(kill_num)  # кеш устарел, чистим
                        del cached_kills[kill]
                        break
                    content += cached['wrapper']  # ускорение загрузки страницы
                    continue

                html_data = load_html_from_url(f"{zkb_url}/cache/24hour/killlistrow/{kill}/")
                if not html_data:
                    continue
                soup = BeautifulSoup(html_data, "lxml")

                info = soup.find('tr', class_='kltbd')
                vics = info['vics']
                #print(f"  vics = {vics}")
                epoch = int(info['date'])
                #print(f"  epoch = {epoch}")
                if (epoch < after_epoch):
                    obsolete_kills.append(kill_num)
                    break  # the rest of the kills are older, we're all done here
                is_victim = our_id in vics.split(',')
                #print(f"  is_victim = {is_victim}")
                el = soup.find('span', {'format': 'format-isk-once'})
                #print(f"  el = {el}")
                raw = el['raw']
                #print(f"  raw = {raw}")
                isk = formatISK(raw)
                isk_num = int(raw.split('.')[0])
                #print(f"  isk = {isk}")
                image = soup.find('span', class_='shipImageSpan')
                if image:
                    image = str(image).replace('src="/', f'src="{zkb_url}/')
                    image = image.replace("src='/", f"src='{zkb_url}/")
                #print(f"  image = {image}")
                if image[-7:] == '</span>':
                    if is_victim:
                        victim = soup.find('td', class_='finalBlow')
                    else:
                        victim = soup.find('td', class_='victim')
                    whom = victim.find_all('a', class_='wrapplease')
                    who_logo = ''
                    for href in whom:
                        who =  href['href']
                        if who[:10] == '/alliance/':
                            who_logo = f'/alliances/{who[10:]}logo?size=32'
                            break
                        elif who[:13] == '/corporation/':
                            who_logo = f'/corporations/{who[13:]}logo?size=32'
                    if who_logo:
                        image = image[:-7] + f'<img alt="" class="alliance" src="https://images.evetech.net{who_logo}">' + '</span>'
                        #print(kill, f"https://images.evetech.net{who_logo}")
                solo = False
                if image[-7:] == '</span>':
                    solo = soup.find_all('a')
                    solo = 1 in [1 for _ in solo if '/solo/' in _['href']]
                    if solo:
                        image = image[:-7] + f'<div class="solo"><font>&nbsp;SOLO&nbsp;</font></div>' + '</span>'
                        #print(f"  solo = {solo}")
                #print(f"  image = {image}")
                points = None
                if image[-7:] == '</span>':
                    zkb_data = load_json_from_url(f"https://zkillboard.com/api/killID/{kill}/")
                    if zkb_data and isinstance(zkb_data, list) and len(zkb_data) == 1 and 'zkb' in zkb_data[0]:
                        if 'points' in zkb_data[0]['zkb']:
                            points = zkb_data[0]['zkb']['points']
                            add_class = 'victim' if is_victim else 'kill'
                            plus_minus = '-' if is_victim else '+'
                            image = image[:-7] + f'<div class="points {add_class}"><font>&nbsp;{points}&nbsp;</font></div>' + '</span>'
                #print(f"  points = {points}")
                wrapper = f"""<div style="display: inline-block; text-align: center;">
{image}
<div class="{'lost' if is_victim else 'killed'}" isk="{isk_num}">{isk}</div>
</div>"""
                #print(wrapper)
                cached_kills.update({kill: {'wrapper': wrapper,  # ускорение загрузки страницы
                                            'epoch': epoch,
                                            'isk': isk_num,
                                            'is_victim': is_victim,
                                            'solo': solo,
                                            'points': points}})
                content += wrapper

        css = ''
        if os.path.exists("streambox.css"):
            try:
                with open("streambox.css", "r", encoding="utf-8") as file:
                    css = "<style>" + file.read() + "</style>"
            except IOError as e:
                print("Error reading streambox.css")

        if not content:
            content = "Failed to load kill list :("
        #else:
        #    lost_isk = 0
        #    killed_isk = 0
        #    for kill, cached in cached_kills.items():
        #        if cached['is_victim']:
        #            lost_isk += cached['isk']
        #        else:
        #            killed_isk += cached['isk']
        #    lost: {formatISK(lost_isk)}<br>
        #    kill: {formatISK(killed_isk)}

        message = f"""<html>
<head>
 <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
 <link rel="stylesheet" href="{zkb_url}/css/streambox.css">
{css}
</head>
<body>
 <div id='content'>{content}</div>
 <div id='promoLong' class='hideme'>zKillboard.com<span id='pathname' style="display: none;"></span></div>
 <div id='promoShort' class='hideme'>zKill<span id='pathname' style="display: none;"></span></div>
 <div id='contenttemp' style='display: none;'></div>
 <table style='display: none;'><tbody id='temp'></tbody></table>
<script>
let current_timeout = 0;
document.addEventListener('DOMContentLoaded', init);
async function init() {{
  clearTimeout(current_timeout);
  current_timeout = setTimeout(fetchKills, 60000);
}}
async function fetchKills() {{
  window.location.reload();
}}
</script>
</body>
</html>"""

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

def run_server(server_class=HTTPServer, handler_class=HttpHandler, address='127.0.0.1', port=8084):
    server_address = (address, port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on port {address}:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
