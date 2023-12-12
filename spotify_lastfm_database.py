import json
import sqlite3
import os
import numpy as np
import spotipy
import requests
from spotipy.oauth2 import SpotifyClientCredentials as SCC
import matplotlib.pyplot as plt

# stary by setting up a connection to SQLite database
# params: database_name
# returns: cursor and connection to database
def setup_database(database_name):
    base_path = os.path.dirname(os.path.realpath(__file__))
    database_connection = sqlite3.connect(os.path.join(base_path, database_name))
    database_cursor = database_connection.cursor()

    return database_cursor, database_connection

# API #1: spotify web api (spotipy) fetches data from spotify playlist
# this is the playlist (billboard hot 100, updates weekly):
# https://open.spotify.com/playlist/6UeSakyzhiEt4NB3UAd6NQ?si=39410f233356484a
# returns: track_data, valence_data, danceability_data, energy_data 
def spotify_data_retrieval():
    # spotify api keys
    spotify_id = "f5cd3aaae8dd450f83cd7c59aabf332e"
    spotify_secret = "efeb4e0b986c485198b441aa58cd43af"
    credential_manager = SCC(client_id=spotify_id, client_secret=spotify_secret)
    spotify_session = spotipy.Spotify(client_credentials_manager=credential_manager)
    billboard_playlist_id = "6UeSakyzhiEt4NB3UAd6NQ"
    # gets the track data from the playlist (includes name, id, artist(s), and popularity)
    track_data = spotify_session.playlist_tracks(billboard_playlist_id, fields='items(track(name,id,popularity,artists))')
    
    # lists to store the 3 audio features for each one of the tracks
    valence_data, danceability_data, energy_data = [], [], []

    # loops through and gets the audio features of each track (valence, danceability, energy)
    for track in track_data['items']:
        track_features = spotify_session.audio_features(track['track']['id'])
        valence_data.append(track_features[0]['valence'])
        danceability_data.append(track_features[0]['danceability'])
        energy_data.append(track_features[0]['energy'])

    return track_data, valence_data, danceability_data, energy_data

# API #2: lastfm api - uses artist name + api key to get more info about each artist
# returns a json of additional info about the artist
def lastfm_data_retrieval(artist_name, lastfm_api_key):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.getinfo",
        "artist": artist_name,
        "api_key": lastfm_api_key,
        "format": "json"
    }
    response = requests.get(base_url, params=params)

    return response.json()

# creates two tables: one table for artist + table one for song
# shared key between tables: artist_id
# need to fix dulicate strings **!
def create_artist_and_song_tables(cursor, connection):
    cursor.execute("CREATE TABLE IF NOT EXISTS Artist (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, lastfm_info TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Song (title TEXT PRIMARY KEY, id TEXT, artist_id INTEGER, popularity INTEGER, valence FLOAT, danceability FLOAT, energy FLOAT)")
    connection.commit()

# puts artist data & song data into sqlite tables
# data comprised of information from both spotify and lastfm
def insert_data_into_tables(track_data, valence, danceability, energy, cursor, connection, lastfm_api_key):
    index = 0
    for track in track_data['items']:
        artist_name = track['track']['artists'][0]['name']
        lastfm_info = lastfm_data_retrieval(artist_name, lastfm_api_key)
        # artist table: name, id, lastfm_info
        cursor.execute("INSERT OR IGNORE INTO Artist (name, lastfm_info) VALUES (?, ?)", (artist_name, json.dumps(lastfm_info)))
        cursor.execute("SELECT id FROM Artist WHERE name = ?", (artist_name,))
        artist_id = cursor.fetchone()[0]
        track_details = track['track']
        # song table: title, id, artist_id, popularity, valence, danceability, energy
        cursor.execute("INSERT OR IGNORE INTO Song (title, id, artist_id, popularity, valence, danceability, energy) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (track_details['name'], track_details['id'], artist_id, track_details['popularity'], valence[index], danceability[index], energy[index]))
        index += 1

    connection.commit()
