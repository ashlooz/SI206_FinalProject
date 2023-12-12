import sqlite3
import matplotlib.pyplot as plt

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
   # popularity x, valence y
   plt.title('Song Popularity vs Valence')
   plt.scatter(popularities, valences, color='red')
   plt.xlabel('Popularity')
   plt.ylabel('Valence')
   plt.grid(True)

   plt.show()

