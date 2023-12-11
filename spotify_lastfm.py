import json
import sqlite3
import os
import numpy as np
import spotipy
import requests
from spotipy.oauth2 import SpotifyClientCredentials as SCC
import matplotlib.pyplot as plt

# first: set up a connection to SQLite database
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
    spotify_id = "32c7e30e325d4b57ba74e2bf47f067b5"
    spotify_secret = "0ae2ba60ce974d8c95a6045fd1967970"
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
    cursor.execute("CREATE TABLE IF NOT EXISTS Artist (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, lastfm_info TEXT)")
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

# visual representation of the data:

# valence = vibes (0.0 - 1.0)
# (0.0 = sad/bad vibes, 1.0 = happy/upbeat vibes)
# popularity = how popular a song is (0 - 100)

# plots the distribution of songs on the billboard hot 100
# compares the popularity of the song to the valence (mood/vibes) of the song
# question this plot addresses: do songs with a higher valence value tend to be more popular?
def popularity_valence_visual(cursor):
   # retrieve the popularity and valence of each song from song table
   cursor.execute("SELECT popularity, valence FROM Song")
   features = cursor.fetchall()
   popularities, valences = zip(*features)

   plt.scatter(popularities, valences, color='red')
   plt.xlabel('Popularity')
   plt.ylabel('Valence')
   plt.title('Song Popularity vs Valence')
   plt.grid(True)

   plt.show()

# plots the distribution of artists (only to 15 shown) on the billboard hot 100
def plot_artist_distribution(cursor):
   # sets a limit on the query to the top 15 artists with the most songs on hot 100 playlist
   cursor.execute("""
       SELECT Artist.name, COUNT(Song.id)
       FROM Song
       JOIN Artist ON Song.artist_id = Artist.id
       GROUP BY Artist.id
       ORDER BY COUNT(Song.id) DESC
       LIMIT 15
   """)
   artist_data = cursor.fetchall()

   # unpacking the fetched data
   artists, song_counts = zip(*artist_data)

   # plotting the data on chart (bar chart with to 15 artists)
   plt.bar(artists, song_counts, color='green')
   plt.xlabel('Artists')
   plt.ylabel('Number of Songs')
   plt.xticks(rotation=90)
   plt.title('Top 15 Artists by Number of Songs on Billboard Hot 100')

   plt.show()

def main():
    # lastfm api key
    lastfm_api_key = "5d2702b8f89733c46c584f393263c35c"
    # set up database
    cursor, connection = setup_database("billboard_hot_100.db")
    
    # make tables
    create_artist_and_song_tables(cursor, connection)

    # get data from spotify and lastfm
    track_data, valence, danceability, energy = spotify_data_retrieval()
    
    # insert data into tables
    insert_data_into_tables(track_data, valence, danceability, energy, cursor, connection, lastfm_api_key)
    
    # plot data for top 15 artists with most songs
    plot_artist_distribution(cursor)

    # plot data for song popularity vs valence
    popularity_valence_visual(cursor)

    # close the connection to database
    connection.close()

if __name__ == "__main__":
    main()
