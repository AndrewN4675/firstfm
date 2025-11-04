import pandas as pd, pickle
import torch
from torch.utils.data import Dataset

# Turn indexes into tensors
class RatingsDataset(Dataset):


    # read csv
    def __init__(self, songsCSV, artistsCSV, songPickle, artistPickle, genrePickle):

        # Get info from the csvs for later
        self.ratingsDataFrame = pd.read_csv(songsCSV)
        self.moviesDataFrame = pd.read_csv(artistsCSV)

        # Grab the serialized information for the genres, user ratings, and movies
        with open(genrePickle, "rb") as file:
            self.genreLE = pickle.load(file)

        with open(songPickle, "rb") as file:
            self.songLE = pickle.load(file)

        with open(artistPickle, "rb") as file:
            self.artistLE = pickle.load(file)

        # Map the human understandable information to what the network understands
        self.ratingsDataFrame["songIndex"] = self.songLE.transform(self.ratingsDataFrame.songID)
        self.ratingsDataFrame["artistIndex"] = self.artistLE.transform(self.ratingsDataFrame.artistID)

        # Merge the movies, ratings, and genres into one dataframe
        combinedDF = self.ratingsDataFrame.merge(self.moviesDataFrame, on="artistID", how="left")

        # Tensorize the pickled information to insert into the network
        self.songIndex = torch.tensor(combinedDF.songIndex.values, dtype=torch.long)
        self.artistIndex = torch.tensor(combinedDF.artistIndex.values, dtype=torch.long)
        self.ratings = torch.tensor(combinedDF.rating.values, dtype=torch.float)
        genreColumns = list(self.genreLE.classes_)
        self.genreValues = torch.tensor(combinedDF[genreColumns].values, dtype=torch.float)
        

    # Get length of dataset
    def __len__(self):
        return len(self.ratings)
    
    # Get a specific movie 
    def __getitem__(self, idx):
        return (
            self.songIndex[idx],
            self.artistIndex[idx],
            self.ratings[idx],
            self.genreValues[idx]
        )