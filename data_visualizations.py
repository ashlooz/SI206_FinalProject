import sqlite3
import matplotlib.pyplot as plt
import statistics
import pandas as pd
import plotly.express as px
import numpy as np
import random
import matplotlib.patches as mpatches

# all of the functions in data_visualizations.py select data from the database and do something with it (i.e. visualization or calculations)
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

   plt.scatter(popularities, valences, color='indigo')
   plt.xlabel('Popularity')
   plt.ylabel('Valence')
   plt.title('Song Popularity vs Valence')
   plt.grid(True)

   plt.show()

# plots the distribution of artists (only to 15 shown) on the billboard hot 100
def plot_artist_distribution(cursor):
    # sets a limit on the query to the top 15 artists with the most songs on hot 100 playlist
    # join is used to merge song table rows with artist table rows (made on the condition that 'artist_id' in song table matches 'id' in artist table)
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

   # plotting the data on chart (bar chart with limit set to 15 artists being displayed)
   plt.bar(artists, song_counts, color='orchid')
   plt.xlabel('Artists')
   plt.ylabel('Number of Songs')
   plt.xticks(rotation=90)
   plt.title('Top 15 Artists by Number of Songs on Billboard Hot 100')
   
   plt.show()

# energy vs. danceability plot
# question to answer from graph: is a higher energy song more likely to be more danceable?
def energy_danceability_visual(cursor):
    # gets the energy and danceability values of each song
    cursor.execute("SELECT energy, danceability FROM Song")
    features = cursor.fetchall()
    energies, danceabilities = zip(*features)

    # makes scatter plot for energy vs danceability
    plt.scatter(energies, danceabilities, color='steelblue')
    plt.xlabel('Energy')
    plt.ylabel('Danceability')
    plt.title('Energy vs Danceability of Songs')
    plt.grid(True)

    plt.show()

# energy distribution of billboard top 100 songs
# does the billboard top 100 have more low, medium, or high energy songs?
def energy_distribution_visual(cursor):
    # get the energy data
    cursor.execute("SELECT energy FROM Song")
    energy_data = cursor.fetchall()
    energies = [float(energy[0]) for energy in energy_data]

    # define the 3 energy categories (low, med, high)
    energy_categories = ["Low", "Medium", "High"]

    # below 0.3 is "low energy"
    # between 0.3 and 0.7 is "medium energy"
    # anything higher than 0.7 is "high energy"
    # count the number of songs in each energy category
    energy_counts = [sum(1 for energy in energies if energy < 0.3),  # low
                     sum(1 for energy in energies if 0.3 <= energy < 0.7),  # medium
                     sum(1 for energy in energies if energy >= 0.7)]  # high

    # makes the bar chart, diff colors for each category
    plt.bar(energy_categories, energy_counts, color=['lightcoral', 'lightblue', 'lightgreen'])
    plt.xlabel('Energy Category')
    plt.ylabel('Number of Songs')
    plt.title('Energy Distribution of Songs on Billboard Hot 100')
    plt.grid(axis='y')

    plt.show()

# calculations from the data: 

# calculates the average valence of all songs in the playlist
def get_average_valence(cursor):
    cursor.execute("SELECT valence FROM Song")
    valence_list = cursor.fetchall()

    if not valence_list:
        # returns a 0 if the list is empty
        return 0

    total_valence = sum(float(valence[0]) for valence in valence_list)
    average_valence = total_valence / len(valence_list)
    return average_valence

# calculates the standard deviation of valences of all songs in the playlist
def get_valence_std_dev(cursor):
    cursor.execute("SELECT valence FROM Song")
    valence_list = cursor.fetchall()

    if len(valence_list) < 2:
        # returns a 0 if the list has less than 2 elements inside
        return 0

    valences = [float(valence[0]) for valence in valence_list]
    valence_std_dev = statistics.stdev(valences)
    return valence_std_dev

# calculates the average play count of all songs in the database (aka the billboard 100 playlist)
def get_average_play_count(cursor):
    cursor.execute("SELECT play_count FROM Song")
    play_count_list = cursor.fetchall()

    if not play_count_list:
        # returns 0 if the list is empty
        return 0

    total_play_count = sum(int(play_count[0]) for play_count in play_count_list)
    average_play_count = total_play_count / len(play_count_list)
    return average_play_count


def valence_to_color(valence):
    """Converts a valence value to a pastel RGBA color string."""
    # base color: 0.0 (sad/blue) to 1.0 (happy/red)
    r = valence
    g = 0.5 * (1 - valence)  # adds in a bit of green to soften the color (less harsh color tone)
    b = 1 - valence

    # mix with white for a "pastel" effect
    mix_with_white = 0.7
    r, g, b = r + (1 - r) * mix_with_white, g + (1 - g) * mix_with_white, b + (1 - b) * mix_with_white

    # formatted as an rgb string (becomes the background color)
    return f'rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, 1)'

def plot_mood_map_interactive(cursor):
    cursor.execute("SELECT valence, energy, title, artist_id FROM Song")
    songs = cursor.fetchall()

    # makes a DataFrame from the data
    df = pd.DataFrame(songs, columns=['Valence', 'Energy', 'Title', 'Artist'])

    # finds average valence
    average_valence = df['Valence'].mean()

    # makes the background color based on average valence
    background_color = valence_to_color(average_valence)

    # uses plotly to create scatter plot
    fig = px.scatter(df, x='Valence', y='Energy', color='Energy',
                     hover_data=['Title', 'Artist'], title='Music Mood Map',
                     labels={'Valence': 'Mood', 'Energy': 'Energy Level'})

    # customizing the layout with the dynamically determined background color
    fig.update_layout(
        xaxis_title='Valence (Mood)',
        yaxis_title='Energy',
        plot_bgcolor=background_color,
        paper_bgcolor=background_color
    )

    fig.show()

    
def create_song_galaxy(cursor):
    # Retrieve song data along with titles and artist names
    cursor.execute("SELECT popularity, valence, energy, title FROM Song")
    songs = cursor.fetchall()

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_facecolor('black')  # Set the background to black
    ax.set_title('Song Galaxy', color='white')
    ax.set_xticks([])
    ax.set_yticks([])

    # Create a starry effect for the background
    for i in range(1500):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        size = random.uniform(0.1, 1)
        ax.scatter(x, y, color='white', alpha=random.uniform(0.1, 0.3), s=size)

    # Plot each song with enhanced visual representation
    for popularity, valence, energy, title in songs:
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        size = np.sqrt(popularity) * 2  # Adjust size scaling based on popularity
        color = plt.cm.spring(energy)  # Color based on energy level
        ax.scatter(x, y, color=color, alpha=0.8, s=size)

        # Show titles for popular songs only to avoid clutter
        if popularity > 70:  # Threshold for displaying song titles
            ax.text(x, y, title, color='white', fontsize=8, ha='center', va='center')

    plt.show()

    
def main():
    # connects to billboard_hot_100 database
    connection = sqlite3.connect("billboard_hot_100.db")
    cursor = connection.cursor()

    # mood map
    plot_mood_map_interactive(cursor)

    # song galaxy
    create_song_galaxy(cursor)
    
    # generate visualizations
    plot_artist_distribution(cursor)
    popularity_valence_visual(cursor)
    energy_danceability_visual(cursor)
    energy_distribution_visual(cursor)
    
    # make calculations and store values accordingly
    valence_standard_deviation = get_valence_std_dev(cursor)
    average_valence = get_average_valence(cursor)
    average_play_count = get_average_play_count(cursor)
    
    # write calculations to calculations_results.txt file
    with open('calculations_results.txt', 'w') as file:
        file.write(f"The valence standard deviation for the songs in the Billboard Top 100 is {valence_standard_deviation}\n")
        file.write(f"The average valence of songs in the Billboard Top 100 is {average_valence}\n")
        file.write(f"The average play count of songs in the Billboard Top 100 is {average_play_count}\n")

    # close db connection
    connection.close()

if __name__ == "__main__":
    main()
