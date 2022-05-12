# sip-pager

Telephone [IVR](https://en.wikipedia.org/wiki/Interactive_voice_response) app to send a "page" to a mobile phone.

## running

Pre-requisites:

- a VPS where you can run a docker container
- an account on a SIP phone server (e.g. [EPVPN](https://eventphone.de/doku/epvpn))
- an account on a [Gotify](https://github.com/gotify/server) instance (to deliver push notifications)
- optional: an Android phone with the [Gotify](https://github.com/gotify/android) client app (to receive push notifications)

First, download the source code onto your VPS:

``` sh
git clone https://github.com/eventphone/hotline
cd hotline
```

Next, enter your credentials:

- update [accfile.conf](config/accfile.conf) with your SIP credentials
- update [gotify.conf](config/gotify.conf) with your Gotify host and API token

Now build the docker container:

``` sh
./build
```

...and run it.

``` sh
./run
```

## hacking

To modify the project, you'll first need to generate the (tiny) build system:

``` sh
./configure
```

You'll only need to run this again if you create new files in `phrases/`.

### changing the logic

Edit `pager/main.py`.

### changing voice prompts

To render prompt audio files using text-to-speech, just rebuild with:

``` sh
ninja
```

### change container config

Just edit `meta/Dockerfile`.

### add new build target

To add new source files to build, edit `meta/build.ninja.j2`. The file will be templated using [`jinja2`](https://jinja.palletsprojects.com/en/3.1.x/). Note that [line statements](https://jinja.palletsprojects.com/en/3.1.x/templates/#line-statements) are enabled with the prefix `##` so that editor syntax highlighting still works.

You don't need to re-run `./configure` after changing `meta/build.ninja.j2`; it will automatically regenerate `build.ninja` the next time `ninja` is run.

## cleaning

To remove the build system, run:

``` sh
./clean
```

This should never be necessary.
