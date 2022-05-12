#!/usr/bin/python3
from configparser import ConfigParser
import logging
import os

from yate.ivr import YateIVR

SOUNDS_PATH = "/opt/sounds"

# for calculating playtime of a SLIN file
SLIN_BITRATE = 15971.43


async def jukebox(config: ConfigParser, ivr: YateIVR, caller_id: str):
    play_audio = os.path.join(SOUNDS_PATH, "phrases", "jukebox.slin")
    additional_timeout_s = float(config['ivr']['prompt_repeat_delay_sec'])

    is_high_priority = False
    repeats = 0
    while repeats < int(config['ivr']['prompt_repeats']):
        await ivr.play_soundfile(play_audio)
        dur = os.path.getsize(play_audio) / SLIN_BITRATE
        digit = await ivr.read_dtmf_symbols(1, timeout_s=dur + additional_timeout_s)

        if digit:
            repeats = 0
        else:
            repeats += 1

        play_audio = os.path.join(SOUNDS_PATH, "phrases", "jukebox.slin")
        additional_timeout_s = float(config['ivr']['prompt_repeat_delay_sec'])

        if digit == "1":
            play_audio = os.path.join(SOUNDS_PATH, "music", "startup.slin")
            repeats = -1
            additional_timeout_s = 1

        if digit == "2":
            play_audio = os.path.join(SOUNDS_PATH, "music", "mym.slin")
            repeats = -1
            additional_timeout_s = 1
