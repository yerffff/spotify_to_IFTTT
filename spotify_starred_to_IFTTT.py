#!/usr/bin/env python
# coding: utf-8

import spotipy
import spotipy.util as util
import ConfigParser
import requests
import json

scope = 'playlist-read-private'
config_file = 'settings.ini'


def load_cfg(filename='settings.ini'):
    """ Charge les paramètres du fichier settings.ini"""
    settings = ConfigParser.ConfigParser()
    settings.read(filename)
    result = {}
    for section in settings.sections():
        result[section]={}
        for option in settings.options(section):
            try:
                result[section][option] = settings.get(section,option)
            except:
                result[section][option] = None
    return result

def get_starred():
    token = util.prompt_for_user_token(config['spotify']['username'],
                                       scope,
                                       config['spotify']['client_id'],
                                       config['spotify']['client_secret'],
                                       "http://localhost")
    sp = spotipy.Spotify(auth=token)
    results = sp.user_playlist(config['spotify']['username'])

    #Le result est paginé (limite à 100 par défaut)
    #On utilise la fonction next pour tout récupérer
    raw_tracks = results['tracks']
    tracks = []
    while raw_tracks:
        for item in raw_tracks['items']:
            track = item['track']
            tracks.append(dict(name=track['name'],
                               artists=track['artists'][0]['name'],
                               album=track['album']['name'],
                               albumart=track['album']['images'][0]['url'],
                               url=track['external_urls']['spotify']))
        raw_tracks = sp.next(raw_tracks)
    return tracks

def push_to_ifttt(song):
    """Envoie la piste vers le channel IFTTT
    Envoie le json directement vers IFTTT; formaté pour un ajout à une spreadsheet google drive
    La clé et le nom de l'event sont récupérés du fichier settings
    """
    url = 'https://maker.ifttt.com/trigger/%s/with/key/%s' % (config['ifttt']['event'], config['ifttt']['key'])
    formatted_song = '%s ||| %s ||| %s ||| =IMAGE("%s";1) ||| %s ' % (song['name'], song['artists'], song['album'], song['albumart'], song['url'])
    #IFTT ne comprend que value1,value2 ou value3 en paramètres
    requests.post(url, data=dict(value1=formatted_song))

if __name__ == '__main__':
    #Récupération de la conf
    config = load_cfg()
    #Récup de la playlist
    songs = get_starred()
    #On compare avec les existants (on n'ajoute que les nouveaux)
    try:
        f = open(config['main']['backup'], 'r')
        old_songs = json.load(f)
        f.close()
    except IOError:
        #fichier inexistant
        old_songs = []
    except ValueError:
        old_songs = []
        f.close()
    for song in songs:
        if song not in old_songs:
            push_to_ifttt(song)

    #sauvegarde du nouveau json
    try:
        f = open(config['main']['backup'], 'w')
        json.dump(songs, f, indent = 4)
        f.close()
    except:
        print "Failed to save song list. New song will be added in double"



