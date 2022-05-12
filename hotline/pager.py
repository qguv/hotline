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

PROMPT_REPEAT_DELAY_S = 3
PROMPT_REPEATS = 5

# for calculating playtime of a SLIN file
SLIN_BITRATE = 15971.43


async def main(ivr: YateIVR):
    caller_id = ivr.call_params.get("caller", "")
    caller_id = re.sub("[^\\d]", "", caller_id)
    caller_id = re.sub("^0000", "+", caller_id)

    callback = caller_id
    priority = 3

    # rotary phone compatibility
    dial_on_timeout = True
    play_audio = os.path.join(SOUNDS_PATH, "phrases", "intro.slin")
    additional_timeout_s = 5

    await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "music", "yintro.slin"), complete=True)

    repeats = 0
    while repeats < PROMPT_REPEATS:
        await ivr.play_soundfile(play_audio)
        dur = os.path.getsize(play_audio) / SLIN_BITRATE
        digit = await ivr.read_dtmf_symbols(1, timeout_s=dur + additional_timeout_s)

        if dial_on_timeout and not digit:
            await send(ivr, callback, caller_id, priority)
            break

        if digit:
            repeats = 0
        else:
            repeats += 1

        dial_on_timeout = False
        play_audio = os.path.join(SOUNDS_PATH, "phrases", "root.slin")
        additional_timeout_s = PROMPT_REPEAT_DELAY_S

        if digit == '*':
            await send(ivr, callback, caller_id, priority)
            break

        if digit == "1":
            play_audio = os.path.join(SOUNDS_PATH, "music", "startup.slin")
            repeats = -1
            additional_timeout_s = 1

        if digit == "2":
            play_audio = os.path.join(SOUNDS_PATH, "music", "mym.slin")
            repeats = -1
            additional_timeout_s = 1

        if digit == "5":
            await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "enter_callback.slin"))
            maybe_callback = (await ivr.read_dtmf_until('#')).rstrip('#')
            if maybe_callback:
                callback = maybe_callback
                await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "callback_updated.slin"), complete=True)

        if digit == "8":
            priority = 8
            await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "priority.slin"), complete=True)

    return await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "goodbye.slin"), complete=True)


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
        await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "page_sent.slin"), complete=True)
        await asyncio.sleep(0.5)


logging.basicConfig(filename=LOG_FILE, filemode="a+")
app = YateIVR()
app.run(main)
