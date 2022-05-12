#!/usr/bin/python3
from configparser import ConfigParser
import functools
import logging
import os
import re

from yate.ivr import YateIVR

from pager import pager

LOG_FILE = "/tmp/corona-ivr.log"
SOUNDS_PATH = "/opt/sounds"
CONFIG_PATH = "/etc/yate"


def read_config():
    config = ConfigParser()

    config.read(os.path.join(CONFIG_PATH, 'gotify.conf'))
    assert 'gotify' in config
    assert 'host' in config['gotify']
    assert 'token' in config['gotify']

    config.read(os.path.join(CONFIG_PATH, 'ivr.conf'))
    assert 'ivr' in config
    assert 'prompt_repeat_delay_sec' in config['ivr']
    assert 'prompt_repeats' in config['ivr']

    return config

async def main(config: ConfigParser, ivr: YateIVR):
    for k, v in ivr.call_params.items():
        print(k, v, sep=": ")

    caller_id = ivr.call_params.get("caller", "")
    caller_id = re.sub("[^\\d]", "", caller_id)
    caller_id = re.sub("^0000", "+", caller_id)

    await ivr.play_soundfile(os.path.join(SOUNDS_PATH, "music", "yintro.slin"), complete=True)
    await pager(config, ivr, caller_id)

if __name__ == "__main__":
    config = read_config()
    logging.basicConfig(filename=LOG_FILE, filemode="a+")
    app = YateIVR()
    app.run(functools.partial(main, config))
