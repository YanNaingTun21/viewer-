
 import io 
 import json 
 import logging 
 import re 
 import textwrap 
 from concurrent.futures import ThreadPoolExecutor, wait 
 from time import gmtime, sleep, strftime, time 
  
 import psutil 
 from fake_headers import Headers, browsers 
 from faker import Faker 
 from requests.exceptions import RequestException 
 from tabulate import tabulate 
 from undetected_chromedriver.patcher import Patcher 
  
 from youtubeviewer import website 
 from youtubeviewer.basics import * 
 from youtubeviewer.config import create_config 
 from youtubeviewer.database import * 
 from youtubeviewer.download_driver import * 
 from youtubeviewer.load_files import * 
 from youtubeviewer.proxies import * 
  
 log = logging.getLogger('werkzeug') 
 log.disabled = True 
  
 SCRIPT_VERSION = '1.8.0' 
  
 print(bcolors.OKGREEN + """ 
  
 Yb  dP  dP"Yb  88   88 888888 88   88 88""Yb 888888 
  YbdP  dP   Yb 88   88   88   88   88 88__dP 88__ 
   8P   Yb   dP Y8   8P   88   Y8   8P 88""Yb 88"" 
  dP     YbodP  `YbodP'   88   `YbodP' 88oodP 888888 
  
                         Yb    dP 88 888888 Yb        dP 888888 88""Yb 
                          Yb  dP  88 88__    Yb  db  dP  88__   88__dP 
                           YbdP   88 88""     YbdPYbdP   88""   88"Yb 
                            YP    88 888888    YP  YP    888888 88  Yb 
 """ + bcolors.ENDC) 
  
 print(bcolors.OKCYAN + """ 
            [ GitHub : https://github.com/MShawon/YouTube-Viewer ] 
 """ + bcolors.ENDC) 
  
 print(bcolors.WARNING + f""" 
 +{'-'*26} Version: {SCRIPT_VERSION} {'-'*26}+ 
 """ + bcolors.ENDC) 
  
 proxy = None 
 status = None 
 start_time = None 
 cancel_all = False 
  
 urls = [] 
 queries = [] 
 suggested = [] 
  
 hash_urls = None 
 hash_queries = None 
 hash_config = None 
  
 driver_dict = {} 
 duration_dict = {} 
 checked = {} 
 summary = {} 
 video_statistics = {} 
 view = [] 
 bad_proxies = [] 
 used_proxies = [] 
 temp_folders = [] 
 console = [] 
  
 threads = 0 
 views = 100 
  
 fake = Faker() 
 cwd = os.getcwd() 
 patched_drivers = os.path.join(cwd, 'patched_drivers') 
 config_path = os.path.join(cwd, 'config.json') 
 driver_identifier = os.path.join(cwd, 'patched_drivers', 'chromedriver') 
  
 DATABASE = os.path.join(cwd, 'database.db') 
 DATABASE_BACKUP = os.path.join(cwd, 'database_backup.db') 
  
 animation = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"] 
 headers_1 = ['Worker', 'Video Title', 'Watch / Actual Duration'] 
 headers_2 = ['Index', 'Video Title', 'Views'] 
  
 width = 0 
 viewports = ['2560,1440', '1920,1080', '1440,900', 
              '1536,864', '1366,768', '1280,1024', '1024,768'] 
  
 referers = ['https://search.yahoo.com/', 'https://duckduckgo.com/', 'https://www.google.com/', 
             'https://www.bing.com/', 'https://t.co/', ''] 
  
 referers = choices(referers, k=len(referers)*3) 
  
 website.console = console 
 website.database = DATABASE 
  
  
 def monkey_patch_exe(self): 
     linect = 0 
     replacement = self.gen_random_cdc() 
     replacement = f"  var key = '${replacement.decode()}_';\n".encode() 
     with io.open(self.executable_path, "r+b") as fh: 
         for line in iter(lambda: fh.readline(), b""): 
             if b"var key = " in line: 
                 fh.seek(-len(line), 1) 
                 fh.write(replacement) 
                 linect += 1 
         return linect 
  
  
 Patcher.patch_exe = monkey_patch_exe 
  
  
 def timestamp(): 
     global date_fmt 
     date_fmt = datetime.now().strftime("%d-%b-%Y %H:%M:%S") 
     return bcolors.OKGREEN + f'[{date_fmt}] | ' + bcolors.OKCYAN + f'{cpu_usage} | ' 
  
  
 def clean_exe_temp(folder): 
     temp_name = None 
     if hasattr(sys, '_MEIPASS'): 
         temp_name = sys._MEIPASS.split('\\')[-1] 
     else: 
         if sys.version_info.minor < 7 or sys.version_info.minor > 11: 
             print( 
                 f'Your current python version is not compatible : {sys.version}') 
             print(f'Install Python version between 3.7.x to 3.11.x to run this script') 
             input("") 
             sys.exit() 
  
     for f in glob(os.path.join('temp', folder, '*')): 
         if temp_name not in f: 
             shutil.rmtree(f, ignore_errors=True) 
  
  
 def update_chrome_version(): 
     link = 'https://gist.githubusercontent.com/MShawon/29e185038f22e6ac5eac822a1e422e9d/raw/versions.txt' 
  
     output = requests.get(link, timeout=60).text 
     chrome_versions = output.split('\n') 
  
     browsers.chrome_ver = chrome_versions 
  
  
 def check_update(): 
     api_url = 'https://api.github.com/repos/MShawon/YouTube-Viewer/releases/latest' 
     try: 
         response = requests.get(api_url, timeout=30) 
  
         RELEASE_VERSION = response.json()['tag_name'] 
  
         if RELEASE_VERSION > SCRIPT_VERSION: 
             print(bcolors.OKCYAN + '#'*100 + bcolors.ENDC) 
             print(bcolors.OKCYAN + 'Update Available!!! ' + 
                   f'YouTube Viewer version {SCRIPT_VERSION} needs to update to {RELEASE_VERSION} version.' + bcolors.ENDC) 
  
             try: 
                 notes = response.json()['body'].split( 
                     'SHA256')[0].split('\r\n') 
                 for note in notes: 
                     if note: 
                         print(bcolors.HEADER + note + bcolors.ENDC) 
             except Exception: 
                 pass 
             print(bcolors.OKCYAN + '#'*100 + '\n' + bcolors.ENDC) 
     except Exception: 
         pass 
  
  
 def create_html(text_dict): 
     if len(console) > 250: 
         console.pop() 
  
     date = f'<span style="color:#23d18b"> [{date_fmt}] | </span>' 
     cpu = f'<span style="color:#29b2d3"> {cpu_usage} | </span>' 
     str_fmt = ''.join( 
         [f'<span style="color:{key}"> {value} </span>' for key, value in text_dict.items()]) 
     html = date + cpu + str_fmt 
  
     console.insert(0, html) 
  
  
 def detect_file_change(): 
     global hash_urls, hash_queries, urls, queries 
  
     if hash_urls != get_hash("urls.txt"): 
         hash_urls = get_hash("urls.txt") 
         urls = load_url() 
         suggested.clear() 
  
     if hash_queries != get_hash("search.txt"): 
         hash_queries = get_hash("search.txt") 
         queries = load_search() 
         suggested.clear() 
  
  
 def direct_or_search(position): 
     keyword = None 
     video_title = None 
     if position % 2: 
         try: 
             method = 1 
             url = choice(urls) 
             if 'music.youtube.com' in url: 
                 youtube = 'Music' 
             else: 
                 youtube = 'Video' 
         except IndexError: 
             raise Exception("Your urls.txt is empty!") 
  
     else: 
         try: 
             method = 2 
             query = choice(queries) 
             keyword = query[0] 
             video_title = query[1] 
             url = "https://www.youtube.com" 
             youtube = 'Video' 
         except IndexError: 
             try: 
                 youtube = 'Music' 
                 url = choice(urls) 
                 if 'music.youtube.com' not in url: 
                     raise Exception 
             except Exception: 
                 raise Exception("Your search.txt is empty!") 
  
     return url, method, youtube, keyword, video_title 
  
  
 def features(driver): 
     if bandwidth: 
         save_bandwidth(driver) 
  
     bypass_popup(driver) 
  
     bypass_other_popup(driver) 
  
     play_video(driver) 
  
     change_playback_speed(driver, playback_speed) 
  
  
 def update_view_count(position): 
     view.append(position) 
     view_count = len(view) 
     print(timestamp() + bcolors.OKCYAN + 
           f'Worker {position} | View added : {view_count}' + bcolors.ENDC) 
  
     create_html({"#29b2d3": f'Worker {position} | View added : {view_count}'}) 
  
     if database: 
         try: 
             update_database( 
                 database=DATABASE, threads=max_threads) 
         except Exception: 
             pass 
  
  
 def set_referer(position, url, method, driver): 
     referer = choice(referers) 
     if referer: 
         if method == 2 and 't.co/' in referer: 
             driver.get(url) 
         else: 
             if 'search.yahoo.com' in referer: 
                 driver.get('https://duckduckgo.com/') 
                 driver.execute_script( 
                     "window.history.pushState('page2', 'Title', arguments[0]);", referer) 
             else: 
                 driver.get(referer) 
  
             driver.execute_script( 
                 "window.location.href = '{}';".format(url)) 
  
         print(timestamp() + bcolors.OKBLUE + 
               f"Worker {position} | Referer used : {referer}" + bcolors.ENDC) 
  
         create_html( 
             {"#3b8eea": f"Worker {position} | Referer used : {referer}"}) 
  
     else: 
         driver.get(url) 
  
  
 def youtube_normal(method, keyword, video_title, driver, output): 
     if method == 2: 
         msg = search_video(driver, keyword, video_title) 
         if msg == 'failed': 
             raise Exception( 
                 f"Can't find this [{video_title}] video with this keyword [{keyword}]") 
  
     skip_initial_ad(driver, output, duration_dict) 
  
     try: 
         WebDriverWait(driver, 10).until(EC.visibility_of_element_located( 
             (By.ID, 'movie_player'))) 
     except WebDriverException: 
         raise Exception( 
             "Slow internet speed or Stuck at reCAPTCHA! Can't load YouTube...") 
  
     features(driver) 
  
     try: 
         view_stat = WebDriverWait(driver, 30).until( 
             EC.presence_of_element_located((By.CSS_SELECTOR, '#count span'))).text 
         if not view_stat: 
             raise WebDriverException 
     except WebDriverException: 
         view_stat = driver.find_element( 
             By.XPATH, '//*[@id="info"]/span[1]').text 
  
     return view_stat 
  
  
 def youtube_music(driver): 
     if 'coming-soon' in driver.title or 'not available' in driver.title: 
         raise Exception( 
             "YouTube Music is not available in your area!") 
     try: 
         WebDriverWait(driver, 10).until(EC.visibility_of_element_located( 
             (By.XPATH, '//*[@id="player-page"]'))) 
     except WebDriverException: 
         raise Exception( 
             "Slow internet speed or Stuck at reCAPTCHA! Can't load YouTube...") 
  
     bypass_popup(driver) 
  
     play_music(driver) 
  
     output = driver.find_element( 
         By.XPATH, '//ytmusic-player-bar//yt-formatted-string').text 
     view_stat = 'music' 
  
     return view_stat, output 
  
  
 def spoof_timezone_geolocation(proxy_type, proxy, driver): 
     try: 
         proxy_dict = { 
             "http": f"{proxy_type}://{proxy}", 
                     "https": f"{proxy_type}://{proxy}", 
         } 
         resp = requests.get( 
             "http://ip-api.com/json", proxies=proxy_dict, timeout=30) 
  
         if resp.status_code == 200: 
             location = resp.json() 
             tz_params = {'timezoneId': location['timezone']} 
             latlng_params = { 
                 "latitude": location['lat'], 
                 "longitude": location['lon'], 
                 "accuracy": randint(20, 100) 
             } 
             info = f"ip-api.com | Lat : {location['lat']} | Lon : {location['lon']} | TZ: {location['timezone']}" 
         else: 
             raise RequestException 
  
     except RequestException: 
         location = fake.location_on_land() 
         tz_params = {'timezoneId': location[-1]} 
         latlng_params = { 
             "latitude": location[0], 
             "longitude": location[1], 
             "accuracy": randint(20, 100) 
         } 
         info = f"Random | Lat : {location[0]} | Lon : {location[1]} | TZ: {location[-1]}" 
  
     try: 
         driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params) 
  
         driver.execute_cdp_cmd( 
             "Emulation.setGeolocationOverride", latlng_params) 
  
     except WebDriverException: 
         pass 
  
     return info 
  
  
 def control_player(driver, output, position, proxy, youtube, collect_id=True): 
     current_url = driver.current_url 
  
     video_len = duration_dict.get(output, 0) 
     for _ in range(90): 
         if video_len != 0: 
             duration_dict[output] = video_len 
             break 
  
         video_len = driver.execute_script( 
             "return document.getElementById('movie_player').getDuration()") 
         sleep(1) 
  
     if video_len == 0: 
         raise Exception('Video player is not loading...') 
  
     actual_duration = strftime( 
         "%Hh:%Mm:%Ss", gmtime(video_len)).lstrip("0h:0m:") 
     video_len = video_len*uniform(minimum, maximum) 
     duration = strftime("%Hh:%Mm:%Ss", gmtime(video_len)).lstrip("0h:0m:") 
  
     if len(output) == 11: 
         output = driver.title[:-10] 
  
     summary[position] = [position, output, f'{duration} / {actual_duration}'] 
     website.summary_table = tabulate( 
         summary.values(), headers=headers_1, numalign='center', stralign='center', tablefmt="html") 
  
     print(timestamp() + bcolors.OKBLUE + f"Worker {position} | " + bcolors.OKGREEN + 
           f"{proxy} --> {youtube} Found : {output} | Watch Duration : {duration} " + bcolors.ENDC) 
  
     create_html({"#3b8eea": f"Worker {position} | ", 
                  "#23d18b": f"{proxy.split('@')[-1]} --> {youtube} Found : {output} | Watch Duration : {duration} "}) 
  
     if youtube == 'Video' and collect_id: 
         try: 
             video_id = re.search( 
                 r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", current_url).group(1) 
             if video_id not in suggested and output in driver.title: 
                 suggested.append(video_id) 
         except Exception: 
             pass 
  
     try: 
         current_channel = driver.find_element( 
             By.CSS_SELECTOR, '#upload-info a').text 
     except WebDriverException: 
         current_channel = 'Unknown' 
  
     error = 0 
     loop = int(video_len/4) 
     for _ in range(loop): 
         sleep(5) 
         current_time = driver.execute_script( 
             "return document.getElementById('movie_player').getCurrentTime()") 
  
         if youtube == 'Video': 
             play_video(driver) 
             random_command(driver) 
         elif youtube == 'Music': 
             play_music(driver) 
  
         current_state = driver.execute_script( 
             "return document.getElementById('movie_player').getPlayerState()") 
         if current_state in [-1, 3]: 
             error += 1 
         else: 
             error = 0 
  
         if error == 10: 
             error_msg = f'Taking too long to play the video | Reason : buffering' 
             if current_state == -1: 
                 error_msg = f"Failed to play the video | Possible Reason : {proxy.split('@')[-1]} not working anymore" 
             raise Exception(error_msg) 
  
         elif current_time > video_len or driver.current_url != current_url: 
             break 
  
     summary.pop(position, None) 
     website.summary_table = tabulate( 
         summary.values(), headers=headers_1, numalign='center', stralign='center', tablefmt="html") 
  
     output = textwrap.fill(text=output, width=75, break_on_hyphens=False) 
     video_statistics[output] = video_statistics.get(output, 0) + 1 
     website.html_table = tabulate(video_statistics.items(), headers=headers_2, 
                                   showindex=True, numalign='center', stralign='center', tablefmt="html") 
  
     return current_url, current_channel 
  
  
 def youtube_live(proxy, position, driver, output): 
     error = 0 
     while True: 
         try: 
             view_stat = driver.find_element( 
                 By.CSS_SELECTOR, '#count span').text 
             if not view_stat: 
                 raise WebDriverException 
         except WebDriverException: 
             view_stat = driver.find_element( 
                 By.XPATH, '//*[@id="info"]/span[1]').text 
         if 'watching' in view_stat: 
             print(timestamp() + bcolors.OKBLUE + f"Worker {position} | " + bcolors.OKGREEN + 
                   f"{proxy} | {output} | " + bcolors.OKCYAN + f"{view_stat} " + bcolors.ENDC) 
  
             create_html({"#3b8eea": f"Worker {position} | ", 
                          "#23d18b": f"{proxy.split('@')[-1]} | {output} | ", "#29b2d3": f"{view_stat} "}) 
         else: 
             error += 1 
  
         play_video(driver) 
  
         random_command(driver) 
  
         if error == 5: 
             break 
         sleep(60) 
  
     update_view_count(position) 
  
  
 def music_and_video(proxy, position, youtube, driver, output, view_stat): 
     rand_choice = 1 
     if len(suggested) > 1 and view_stat != 'music': 
         rand_choice = randint(1, 3) 
  
     for i in range(rand_choice): 
         if i == 0: 
             current_url, current_channel = control_player( 
                 driver, output, position, proxy, youtube, collect_id=True) 
  
             update_view_count(position) 
  
         else: 
             print(timestamp() + bcolors.OKBLUE + 
                   f"Worker {position} | Suggested video loop : {i}" + bcolors.ENDC) 
  
             create_html( 
                 {"#3b8eea": f"Worker {position} | Suggested video loop : {i}"}) 
  
             try: 
                 output = play_next_video(driver, suggested) 
             except WebDriverException as e: 
                 raise Exception( 
                     f"Error suggested | {type(e).__name__} | {e.args[0] if e.args else ''}") 
  
             print(timestamp() + bcolors.OKBLUE + 
                   f"Worker {position} | Found next suggested video : [{output}]" + bcolors.ENDC) 
  
             create_html( 
                 {"#3b8eea": f"Worker {position} | Found next suggested video : [{output}]"}) 
  
             skip_initial_ad(driver, output, duration_dict) 
  
             features(driver) 
  
             current_url, current_channel = control_player( 
                 driver, output, position, proxy, youtube, collect_id=False) 
  
             update_view_count(position) 
  
     return current_url, current_channel 
  
  
 def channel_or_endscreen(proxy, position, youtube, driver, view_stat, current_url, current_channel): 
     option = 1 
     if view_stat != 'music' and driver.current_url == current_url: 
         option = choices([1, 2, 3], cum_weights=(0.5, 0.75, 1.00), k=1)[0] 
  
         if option == 2: 
             try: 
                 output, log, option = play_from_channel( 
                     driver, current_channel) 
             except WebDriverException as e: 
                 raise Exception( 
                     f"Error channel | {type(e).__name__} | {e.args[0] if e.args else ''}") 
  
             print(timestamp() + bcolors.OKBLUE + 