#!/usr/bin/python3
import asyncio
import datetime
import logging
import os
import re
import uuid

import requests
from yate.protocol import MessageRequest
from yate.ivr import YateIVR

LOG_FILE = "/tmp/corona-ivr.log"

SOUNDS_PATH = "/opt/sounds"
URL = "https://hookb.in/yDL1djMbXZUeWb73yzkg"
API_TOKEN = "12345"
FORWARD_PHONE_ADDRESS = "sip/2001"
LINE = "test_line"
SIP_FROM_HEADER = "<sip:1234@eventphone>"

FALLBACK_FILES_DIR = "/tmp"


async def main(ivr: YateIVR):
    caller_id = ivr.call_params.get("caller", "")
    caller_id = re.sub("[^\\d]", "", caller_id)
    caller_id = re.sub("^\\+", "00", caller_id)

    callback = caller_id
    priority = 3

    # rotary phone compatibility
    dial_on_timeout = True
    menu_timeout_s = 13.37
    play_audio = os.path.join(SOUNDS_PATH, "api", "intro.slin")

    await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "yintro.slin"), complete=True)

    while True:
        await ivr.play_soundfile(play_audio)

        digit = await ivr.read_dtmf_symbols(1, timeout_s=menu_timeout_s)
        if dial_on_timeout and not digit:
            return await send(ivr, callback, caller_id, priority)

        dial_on_timeout = False
        menu_timeout_s = 13.37
        play_audio = os.path.join(SOUNDS_PATH, "api", "root.slin")

        if digit == '*':
            return await send(ivr, callback, caller_id, priority)

        if digit == "1":
            menu_timeout_s = 70.0
            play_audio = os.path.join(SOUNDS_PATH, "music", "startup.slin")

        if digit == "5":
            await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "api", "enter_callback.slin"))
            maybe_callback = (await ivr.read_dtmf_until('#')).rstrip('#')
            if maybe_callback:
                callback = maybe_callback
                await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "api", "callback_updated.slin"), complete=True)

        if digit == "8":
            priority = 8
            await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "api", "priority.slin"), complete=True)


async def send(ivr: YateIVR, callback: str, caller_id: str, priority: int):
    message = f"tel:{callback}"
    if callback != caller_id:
        message += f" (from tel:{caller_id})"
    data = {
        "title": "EPVPN page received",
        "message": message,
        "priority": priority,
    }
    headers = {
        "X-Gotify-Key": API_TOKEN,
    }
    success = True
    error_message = ""
    try:
        api_result = requests.post(URL, data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        success = False
        error_message = str(e) + str(e.message)

    if success and api_result.status_code != 200:
        success = False
        error_message = "HTTP error: " + str(api_result.status_code)

    if not success:
        fallback_filename = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-") + uuid.uuid4().hex + "response.sbj"
        fallback_file = os.path.join(FALLBACK_FILES_DIR, fallback_filename)
        with open(fallback_file, "w") as f:
            f.write(error_message + "\n")
            f.write(repr(data) + "\n")
            f.write(repr(headers) + "\n")
        print(error_message)
    else:
        await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "api", "page_sent.slin"), complete=True)
        await asyncio.sleep(0.5)


logging.basicConfig(filename=LOG_FILE, filemode="a+")
app = YateIVR()
app.run(main)
