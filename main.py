from spotify_lastfm_database import (
    setup_database,
    spotify_data_retrieval,
    lastfm_data_retrieval,
    create_artist_and_song_tables,
    insert_data_into_tables)

from visualizations import plot_artist_distribution, popularity_valence_visual

def main():
    # lastfm api key
    lastfm_api_key = "975e6d8efe97116b6f9635ba43e16e6e"
    
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
