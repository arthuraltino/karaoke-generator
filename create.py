#!/usr/bin/env python
import sys
import subprocess
import json
import os
import hashlib
import whisper_timestamped as whisper
from datetime import timedelta

CACHE_FOLDER = ".cache"

def load_transcription_result(audio_filename):
    cache_filename = get_cache_filename(audio_filename)

    if os.path.isfile(cache_filename):
        with open(cache_filename, "r") as cache_file:
            return json.load(cache_file)

    audio = whisper.load_audio(audio_filename)
    model = whisper.load_model("medium.en", device="cpu")
    result = whisper.transcribe(model, audio, language="en")

    with open(cache_filename, "w") as cache_file:
        json.dump(result, cache_file, indent=2)

    return result


def calculate_singing_percentage(audio_filename):
    result = load_transcription_result(audio_filename)

    # Calculate total seconds of singing
    total_singing_duration = sum(segment["end"] - segment["start"] for segment in result["segments"])

    # Calculate song duration using ffprobe
    duration_command = ['ffprobe', '-i', audio_filename, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")]
    duration_output = subprocess.check_output(duration_command, universal_newlines=True)
    song_duration = float(duration_output)

    # Calculate singing percentage
    singing_percentage = (total_singing_duration / song_duration) * 100

    return result, singing_percentage, total_singing_duration, song_duration


def get_cache_filename(audio_filename):
    filename = os.path.split(audio_filename)[1]
    hash_value = get_file_hash(audio_filename)
    cache_filename = os.path.join(CACHE_FOLDER, filename + "_" + hash_value + ".json")
    return cache_filename


def get_file_hash(filename):
    hasher = hashlib.md5()
    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_cache_folder():
    if not os.path.exists(CACHE_FOLDER):
        os.makedirs(CACHE_FOLDER)


def format_time(seconds):
    return "{:02}:{:02}".format(int(seconds // 60), int(seconds % 60))


if len(sys.argv) < 2:
    print("Please provide the audio file name as the first command-line parameter.")
    sys.exit(1)

audio_filename = sys.argv[1]
create_cache_folder()

result, singing_percentage, total_singing_duration, song_duration = calculate_singing_percentage(audio_filename)
segment_count = len(result["segments"])

print("Total Song Duration: {}".format(format_time(song_duration)))
print("Total Singing Duration: {}".format(format_time(total_singing_duration)))
print("Singing Percentage: {:.2f}%".format(singing_percentage))
print("Total Lyric Segments: {}".format(segment_count))
