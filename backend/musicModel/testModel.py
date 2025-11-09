from recommendation import recommendationSystemTest

if __name__ == "__main__":

    # From the name of the movie + year, find similar movies contained in the model
    movieTitle = input("Enter song title: ")
    recommendedMovie = recommendationSystemTest(movieTitle, k=10)
    print("Top 10 Similar songs: ")
    for movie, artist, score in recommendedMovie:
        print(f"Song: {movie} by {artist} (sim={score:.3f})")