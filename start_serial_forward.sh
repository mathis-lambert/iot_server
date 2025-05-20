#!/bin/zsh
socat -d -d TCP-LISTEN:9090,fork,reuseaddr FILE:/dev/tty.debug-console,b115200,raw
