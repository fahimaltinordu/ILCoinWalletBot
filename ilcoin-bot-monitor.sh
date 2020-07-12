#!/bin/bash

myscript(){
    python3 command.py
}

until myscript; do
    echo "'command.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done