import sqlite3
import matplotlib.pyplot as plt
import statistics

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
        # Returns 0 if the list is empty
        return 0

    total_play_count = sum(int(play_count[0]) for play_count in play_count_list)
    average_play_count = total_play_count / len(play_count_list)
    return average_play_count

def main():
    # connects to billboard_hot_100 database
    connection = sqlite3.connect("billboard_hot_100.db")
    cursor = connection.cursor()

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
