import json
import sqlite3
import os
import requests
from spotipy.oauth2 import SpotifyClientCredentials as SCC
import spotipy

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
def spotify_data_retrieval(spotify_id, spotify_secret):
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

# creates two tables: one table for artist + table one for song
# shared key between tables: artist_id
def create_artist_and_song_tables(cursor, connection):
    # artist table - name text must be unique = no duplicate string data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Artist (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT UNIQUE)
    """)
    # song table with corresponding id, popularity, artist_id, valence, daceability, energy, and play count
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Song (
        title TEXT PRIMARY KEY, 
        id TEXT,
        artist_id INTEGER, 
        popularity INTEGER, 
        valence FLOAT, 
        danceability FLOAT, 
        energy FLOAT,
        play_count INTEGER)
    """)
    connection.commit()

# gets the number of times song has been played for the specified track (data from lastfm api)
def get_lastfm_play_count(track_title, artist_name, lastfm_api_key):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    # parameters for api request
    params = {
        "method": "track.getInfo",
        "track": track_title,
        "artist": artist_name,
        "api_key": lastfm_api_key,
        "format": "json"
    }
    # first makes api request
    response = requests.get(base_url, params=params)
    # then parses the json response
    track_info = response.json()
    
    # gets play count --> or play count will default to 0 if not applicable
    play_count = track_info.get('track', {}).get('playcount', 0)
    return int(play_count)

# puts artist data & song data into sqlite tables
# data comprised of information from both spotify and lastfm
def insert_data_into_tables(track_data, valence, danceability, energy, cursor, connection, lastfm_api_key):
    cursor.execute("SELECT COUNT(*) FROM Song")
    # figures out the current # of songs in the song table
    count = cursor.fetchone()[0]

    # starting index is where count left off
    start_index = count
    end_index = start_index + 25 # index to end at will be 25 max from the starting index

    # iteration for each unique track to add its corresponding data to the table
    for i in range(start_index, min(end_index, len(track_data['items']))):
        track = track_data['items'][i]['track']
        artist_name = track['artists'][0]['name']

        # gets the play count from last fm api
        play_count = get_lastfm_play_count(track['name'], artist_name, lastfm_api_key)

        # puts the artist name into the artist table
        # also ignores duplicate data (prevents duplicate string data)
        cursor.execute("INSERT OR IGNORE INTO Artist (name) VALUES (?)", (artist_name,))
        # get artist id
        cursor.execute("SELECT id FROM Artist WHERE name = ?", (artist_name,))
        artist_id = cursor.fetchone()[0]
        # adds the track info to song table
        cursor.execute("""
        INSERT OR IGNORE INTO Song 
        (title, id, artist_id, popularity, valence, danceability, energy, play_count) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
        (track['name'], track['id'], artist_id, track['popularity'], valence[i], danceability[i], energy[i], play_count))

    connection.commit()

def main():
    # keys
    spotify_id = "f085180bc7734d74ad93260bc79e49a4"
    spotify_secret = "641e6fab2a7b4b608e7053e80c376b8d"
    lastfm_api_key = "975e6d8efe97116b6f9635ba43e16e6e"

    # set up database connection
    cursor, connection = setup_database("billboard_hot_100.db")

    # make the artist table and song table
    create_artist_and_song_tables(cursor, connection)

    # get data from spotify api
    track_data, valence, danceability, energy = spotify_data_retrieval(spotify_id, spotify_secret)

    # insert data into tables
    insert_data_into_tables(track_data, valence, danceability, energy, cursor, connection, lastfm_api_key)

    connection.close()

if __name__ == "__main__":
    main()
