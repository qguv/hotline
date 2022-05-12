#!/usr/bin/python3
import asyncio
from configparser import ConfigParser
import datetime
import os
import uuid

import requests
from yate.ivr import YateIVR

SOUNDS_PATH = "/opt/sounds"
FALLBACK_FILES_DIR = "/tmp"

# for calculating playtime of a SLIN file
SLIN_BITRATE = 15971.43


async def pager(config: ConfigParser, ivr: YateIVR, caller_id: str):
    callback = caller_id
    is_high_priority = False

    # rotary phone compatibility
    dial_on_timeout = True
    play_audio = os.path.join(SOUNDS_PATH, "phrases", "page_rotary.slin")
    additional_timeout_s = 5

    repeats = 0
    while repeats < int(config['ivr']['prompt_repeats']):
        await ivr.play_soundfile(play_audio)
        dur = os.path.getsize(play_audio) / SLIN_BITRATE
        digit = await ivr.read_dtmf_symbols(1, timeout_s=dur + additional_timeout_s)

        if dial_on_timeout and not digit:
            await send(config, ivr, callback, caller_id, is_high_priority)
            break

        if digit:
            repeats = 0
        else:
            repeats += 1

        dial_on_timeout = False
        play_audio = os.path.join(SOUNDS_PATH, "phrases", "page.slin")
        additional_timeout_s = float(config['ivr']['prompt_repeat_delay_sec'])

        if digit == '*':
            await send(config, ivr, callback, caller_id, is_high_priority)
            break

        if digit == "5":
            await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "phrases", "enter_callback.slin"))
            maybe_callback = (await ivr.read_dtmf_until('#')).rstrip('#')
            if maybe_callback:
                callback = maybe_callback
                play_audio = os.path.join(SOUNDS_PATH, "phrases", "callback_updated.slin")
                repeats = -1
                additional_timeout_s = 1

        if digit == "8":
            is_high_priority = not is_high_priority
            play_audio = os.path.join(SOUNDS_PATH, "phrases", "priority_high.slin" if is_high_priority else "priority_normal.slin")
            repeats = -1
            additional_timeout_s = 1


async def send(config: ConfigParser, ivr: YateIVR, callback: str, caller_id: str, is_high_priority: bool):
    message = f"tel:{callback}"
    if callback != caller_id:
        message += f" (from tel:{caller_id})"
    data = {
        "title": "EPVPN page received",
        "message": message,
        "priority": 8 if is_high_priority else 3,
    }
    headers = {
        "X-Gotify-Key": config['gotify']['token'],
    }
    success = True
    error_message = ""
    try:
        api_result = requests.post(f"https://{config['gotify']['host']}/message", data=data, headers=headers)
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
