#!/bin/zsh
# @raycast.schemaVersion 1
# @raycast.title Obsidian Clipper
# @raycast.mode silent

nohup /Users/arthurstubbings/obsidian-clipper/venv/bin/python /Users/arthurstubbings/obsidian-clipper/clip.py > /tmp/obsidian-clipper.log 2>&1 &
