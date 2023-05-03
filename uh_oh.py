import os
import openai
import mido
from mido import MidiFile
from music21 import converter, instrument, note, chord, stream
from gtts import gTTS
from pydub import AudioSegment
from midi2audio import FluidSynth
import xml.etree.ElementTree as ET
import subprocess

def fix_wav_file(input_file, output_file):
    # Convert the input file to MP3 format
    temp_mp3_file = 'temp.mp3'
    subprocess.run(['ffmpeg', '-i', input_file, temp_mp3_file])

    # Convert the MP3 file back to WAV format
    subprocess.run(['ffmpeg', '-i', temp_mp3_file, output_file])

    # Delete the temporary MP3 file
    os.remove(temp_mp3_file)


def read_api_key(filepath):
    with open(filepath, 'r') as file:
        api_key = file.read().strip()
    return api_key

def read_lyrics_file(filepath):
    with open(filepath, "r") as file:
        lyrics = file.read()
    return lyrics

def extract_melody_from_midi(filepath):
    melody = []
    mid = MidiFile(filepath)
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'note_on':
                melody.append(msg.note)
    return melody

def melody_to_string(melody):
    return ' '.join(str(note) for note in melody)

def align_lyrics_to_melody(lyrics, melody):
    lyrics = ' '.join(lyrics.split()[:200])
    melody = ' '.join(melody.split()[:100])

    prompt = f"Adjust the following lyrics to fit the given melody:\n\nLyrics:\n{lyrics}\n\nMelody:\n{melody}\n\nAdjusted Lyrics:"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )

    aligned_lyrics = response.choices[0].text.strip()
    return aligned_lyrics

def aligned_lyrics_to_musicxml(aligned_lyrics, output_musicxml_file):
    # Create a new music21 stream
    s = stream.Stream()

    # Convert the aligned lyrics string to a list of words
    lyrics_list = aligned_lyrics.split()

    # Add each lyric as a note to the stream
    for lyric in lyrics_list:
        n = note.Note()
        n.lyric = lyric
        s.append(n)

    # Write the stream to a MusicXML file
    s.write('musicxml', fp=output_musicxml_file)

def extract_lyrics_from_musicxml(musicxml_file):
    melody = converter.parse(musicxml_file)
    melody_notes = melody.flat.notes
    lyrics = []

    for n in melody_notes:
        if isinstance(n, note.Note) or isinstance(n, chord.Chord):
            if n.lyric:
                lyrics.append(n.lyric)

    return lyrics

def lyrics_to_speech(lyrics, mp3_file):
    lyrics_text = ' '.join(lyrics)
    tts = gTTS(lyrics_text, lang='en', slow=False)
    tts.save(mp3_file)

def midi_to_wav(midi_file, wav_file):
    soundfont_path = "/path/to/rapsongs/GeneralUser_GS_v1.471.sf2"
    fs = FluidSynth(sound_font=soundfont_path)
    fs.midi_to_audio(midi_file, wav_file)

def merge_wav_files(melody_wav_file, lyrics_wav_file, output_wav_file):
    melody_audio = AudioSegment.from_wav(melody_wav_file)
    lyrics_audio = AudioSegment.from_wav(lyrics_wav_file)

    merged_audio = melody_audio.overlay(lyrics_audio)
    merged_audio.export(output_wav_file, format="wav")



def main():
    api_key_filepath = 'gpt_key.txt'
    openai.api_key = read_api_key(api_key_filepath)

    melody_midi_file = 'kanyewestgolddigger.mid'
    lyrics_file = 'love_songs.txt'
    output_musicxml_file = 'output_musicxml.xml'
    melody_wav_file = 'melody_wav_file.wav'
    lyrics_wav_file = 'lyrics.wav'
    final_output_wav_file = 'final_output.wav'

    # Read the lyrics from the file
    your_lyrics = read_lyrics_file(lyrics_file)

    # Extract the melody from the MIDI file and convert it to a string
    midi_melody = extract_melody_from_midi(melody_midi_file)
    your_melody = melody_to_string(midi_melody)

    # Align the lyrics to the melody
    aligned_lyrics = align_lyrics_to_melody(your_lyrics, your_melody)
    print("Aligned Lyrics:\n", aligned_lyrics)

    # Save the aligned lyrics to MusicXML
    aligned_lyrics_to_musicxml(aligned_lyrics, output_musicxml_file)

    # Extract lyrics from the MusicXML file
    lyrics_from_musicxml = extract_lyrics_from_musicxml(output_musicxml_file)

    # Create the lyrics WAV file
    lyrics_to_speech(lyrics_from_musicxml, lyrics_wav_file)

    # Create the melody WAV file
    midi_to_wav(melody_midi_file, melody_wav_file)

    # Fix the 'lyrics.wav' file
    fixed_lyrics_wav_file = 'fixed_lyrics.wav'
    fix_wav_file(lyrics_wav_file, fixed_lyrics_wav_file)

    # Merge the melody and lyrics WAV files
    final_output_wav_file = 'final_output.wav'
    merge_wav_files(melody_wav_file, fixed_lyrics_wav_file, final_output_wav_file)
if __name__ == '__main__':
    main()



