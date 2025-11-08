from recommendation import recommendationSystemTest

if __name__ == "__main__":

    # From the name of the movie + year, find similar movies contained in the model
    movieTitle = input("Enter song embid: ")
    recommendedMovie = recommendationSystemTest(movieTitle, k=10)
    print("Top 10 Similar movies: ")
    for movie, score in recommendedMovie:
        print(f"Movie {movie} (sim={score:.3f})")