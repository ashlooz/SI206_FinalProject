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
    # retrieve the number of rows already present in the Song table in sqlite
    cursor.execute("SELECT COUNT(*) FROM Song")
    count = cursor.fetchone()[0] # this will find the first (& only) item from the result, telling us how many songs are in the database

    # figures out where the start and end indices must be for this run
    start_index = count # start at the current song count (pick up from where we last left off if applicable)
    end_index = start_index + 25 # stop adding at end_index for this run (i.e. once a max of 25 new items are added)

    for i in range(start_index, min(end_index, len(track_data['items']))):
        # track and artist information
        track = track_data['items'][i]['track']
        artist_name = track['artists'][0]['name']
        # additional lastfm information
        lastfm_info = lastfm_data_retrieval(artist_name, lastfm_api_key)

        # inserts the artists info into Artist table (will ignore duplicate data)
        cursor.execute("INSERT OR IGNORE INTO Artist (name, lastfm_info) VALUES (?, ?)", (artist_name, json.dumps(lastfm_info)))
        
        # gets the artist id from the Artist table
        cursor.execute("SELECT id FROM Artist WHERE name = ?", (artist_name,))
        artist_id = cursor.fetchone()[0]

        # inserts the song info into the Song table (also ignores duplicates)
        cursor.execute("INSERT OR IGNORE INTO Song (title, id, artist_id, popularity, valence, danceability, energy) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (track['name'], track['id'], artist_id, track['popularity'], valence[i], danceability[i], energy[i]))

    # commit changes
    connection.commit()

# write out json file for top artist***

def main():
    # keys
    spotify_id = "3681517a0b5b46ff9b8f880c64c32fce"
    spotify_secret = "a0df66c9cfba4f41bf393cab9060f7b4"
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
