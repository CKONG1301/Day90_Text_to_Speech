from tkinter import *
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader
import os
from dotenv import load_dotenv
import requests
from playsound import playsound
from base64 import b64decode
import time
import threading


is_continue = False
load_dotenv()


def handler_timer(new_index):
    global is_continue
    last_line = int(textbox.index('end-1c').split('.')[0])
    while is_continue:
        current_line = int(new_index.split('.')[0])
        label_line.config(text=f'Line: {current_line}/{last_line}')
        # Get first post of a line or a sentence.
        new_index = textbox.index(f'{new_index} wordstart')
        # Get last position of a sentence.
        next_index = textbox.search('.', f'{new_index} + 1chars')
        # Highlight the section that is current read.
        textbox.tag_add('read_line', new_index, next_index)
        textbox.tag_config('read_line', foreground='blue')
        line = textbox.get(new_index, next_index).replace('.', '')
        # Handle textbox that wrap back to the top when reach end of PDF.
        if next_index <= new_index:
            line = textbox.get(new_index, END).replace('.', '')
            read_stop()
        else:
            new_index = next_index
            textbox.see(f'{next_index} + 8lines')
            time.sleep(0.5)
        text_to_speech(line)
        textbox.tag_config('read_line', foreground='black')
        textbox.tag_delete('read_line')
    
    
def read_stop():
    global is_continue
    # Toggle read start/stop.
    is_continue = not is_continue
    if is_continue:
        btn_read.config(text="STOP READ")
    else:
        btn_read.config(text="START READ")


def text_to_speech(text):
    url = os.getenv('VOICE_RSS_URL')
    query = {
        "key": os.getenv('VOICE_RSS_API'),
        "src": text,
        "hl": "en-us",
        "r": "0",
        "c": "mp3",
        "f": "48khz_16bit_mono",
        # 'b64'=False for saving into file.
        "b64": False,
    }
    response = requests. request('GET', url, params=query)
    audio_file = 'audio.mp3'
    with open(audio_file, 'w+b') as file:
        if query['b64']:
            content = b64decode(response.content)
        else:
            content = response.content
        file.write(bytearray(content))
    # Get current fullpath name.
    full_path = os.getcwd()
    audio_file = full_path + f'/{audio_file}'
    # playsound use forward slash, and need fullpath name.
    audio_file = audio_file.replace("\\", '/')
    playsound(audio_file)
    os.remove(audio_file)


def click(event):
    global timer, is_continue
    new_index = textbox.index(CURRENT)
    if is_continue and not timer.is_alive():
        timer = threading.Thread(target=handler_timer, args=(new_index,), name='timer')
        timer.start()


def open_file():
    filename = filedialog.askopenfilename(
        filetypes=(("PDF File", "*.pdf"),
                   ("all files", "*.*"))
    )
    reader = PdfReader(filename)
    num_pages = len(reader.pages)
    textbox.config(state='normal')
    for n in range(num_pages-1, -1, -1):
        page = reader.pages[n]
        text = page.extract_text()
        textbox.insert('1.0', text)
    textbox.config(state='disabled')


# Create the window
window = Tk()
window.title("PDF To Speech Conversion")
window.minsize(width=600, height=450)
window.config(padx=20, pady=10)
# Create button
btn_browse = Button(text="Select PDF", width=20, command=open_file)
btn_browse.grid(row=0, column=0, pady=5, sticky=W)
btn_end = Button(window, text="EXIT", width=20, command=lambda: window.destroy())
btn_end.grid(row=0, column=1, pady=5, sticky=E)
btn_read = Button(window, text="START READ", width=20, command=read_stop)
btn_read.grid(row=2, column=1, pady=5, sticky=E)
# Crete label.
label_line = Label(window, text='Line: ', width=20)
label_line.grid(row=2, column=0, pady=5, sticky=W)
# Create text to display the text
textbox = Text(height=20, width=60, pady=10, takefocus=False, font='Arial, 12', wrap=WORD)
# textbox.bind('<KeyPress>', click)
textbox.bind('<Button-1>', click)
textbox.grid(row=1, column=0, columnspan=2)
# Create scrollbar.
yscroll = Scrollbar(command=textbox.yview, elementborderwidth=2, cursor='hand2', width=30, orient='vertical')
yscroll.grid(row=1, column=2, sticky=N+S+E)
textbox.config(yscrollcommand=yscroll.set)
timer = threading.Thread(target=handler_timer, name='timer')
# Must put at the end
window.mainloop()

