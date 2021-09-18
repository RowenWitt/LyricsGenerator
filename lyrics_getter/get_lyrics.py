from dotenv import load_dotenv, find_dotenv
import bs4
import os
import re
import requests
import time
from typing import List, Dict, Tuple

load_dotenv(find_dotenv())


gid = os.getenv('GENIUS_ID')
gsec = os.getenv('GENIUS_SECRET')
gtok = os.getenv('GENIUS_TOKEN')


class Lyrics(object):

    def __init__(self):
        self.gen_url = 'https://genius.com/'
        self.list_url = 'https://www.song-list.net/'

    def just_replace_strings_with_dashes(self, artist: str) -> str:
        """
        replaces ' ' with '-', that's it
        """
        data = re.sub(' ', '-', artist)

        return data

    def just_replace_strings_with_nothing(self, artist: str) -> str:
        """
        replaces ' ' with '', that's it
        """
        data = re.sub(' ', '', artist)

        return data

    def get_song_list(self, artist: str) -> List[str]:
        """
        Gets discography of artist for lyric grabbing
        I'm limited by the technology of my time (current regex understanding)
        so this is pretty pretty pretty inneficient but reaching
        marginal returns regarding regex iteration
        """
        artist = self.just_replace_strings_with_nothing(artist)

        url = self.list_url + artist + '/songs'

        resp = requests.get(url)

        content = bs4.BeautifulSoup(resp.content)

        song_list = content.text[content.text.index(
            'MP3s') + 5:content.text.index('About Song List')]

        song_list = re.sub('\n', ',', song_list)
        song_list = re.sub(',+', ',', song_list)
        song_list = re.sub(', ,', ', ', song_list)

        song_list = re.split(',', song_list)
        for i in range(len(song_list)):
            song_list[i] = song_list[i].lstrip(' ')
            song_list[i] = re.sub("[.,']", '', song_list[i])
            song_list[i] = re.sub("&", 'and', song_list[i])
            song_list[i] = re.sub('\s+', ' ', song_list[i])

        song_list = [i for i in song_list if i != '']

        return song_list

    def clean_lyrics_response(self, lyrics: str) -> str:
        """
        Cleans lyric response
        """
        lyrics = re.sub("'", '', lyrics)
        lyrics = re.sub('\W', ' ', lyrics)
        needs_space = re.finditer(r'([a-z][A-Z])', lyrics)

        for i in needs_space:
            group = i.group()[-2:]
            lyrics = re.sub(group, '{} {}'.format(group[0], group[1]), lyrics)

        lyrics = re.split('(Verse|Chorus|Outro)', lyrics)
        keep = []
        for i in range(len(lyrics)):
            if lyrics[i] != ' ':
                keep.append(lyrics[i])

        lyrics = keep
        del keep

        titles = lyrics[::2]
        words = lyrics[1::2]
        for i in range(len(titles)):
            words[i] = titles[i] + words[i]

        lyrics = "".join(i + ' \n ' for i in words)

        return lyrics

    def get_genius_page(self, artist: str, song: str) -> str:
        """
        gets page of lyrics from genius
        """

        artist = self.just_replace_strings_with_dashes(artist)
        song = self.just_replace_strings_with_dashes(song)

        url = self.gen_url + artist + '-' + song + '-lyrics'

        resp = requests.get(url)

        if resp.status_code == 200:
            try:
                content = bs4.BeautifulSoup(resp.content)
                lyrics = content.text[content.text.rindex(
                    '[Verse 1]'):content.text.index('Embed')]
                lyrics = self.clean_lyrics_response(lyrics)
                return lyrics

            except (ValueError, IndexError) as e:
                print('Lyrics not found {}, due to error {}'.format(song, e))

            try:
                lyrics = content.text[content.text.rindex(
                    '[Verse]'):content.text.index('Embed')]
                lyrics = self.clean_lyrics_response(lyrics)
                return lyrics

            except ValueError as e:
                print(
                    'Lyrics not found {}, due to error {}, single verse song'.format(song, e))

    def get_all_artists_lyrics(self, artist: str) -> List[Dict]:
        """
        Gets all songs lyrics for a given artist
        artist input should look like "queens of the stone age"
        """
        artist = artist.lower()
        song_list = self.get_song_list(artist)

        lyric_dict = {}
        for i in song_list:
            lyrics = self.get_genius_page(artist, i)
            lyric_dict[i] = lyrics

        return lyric_dict
