import pandas as pd, pickle
import torch
from torch.utils.data import Dataset

# Turn indexes into tensors
class TrainTestVal(Dataset):

    # read csv
    def __init__(self, trainValTestCSV, songPickle, artistPickle, genrePickle):

        # Get info from the csvs for later
        self.trainTestValDataFrame = pd.read_csv(trainValTestCSV)

        # Grab the serialized information for the genres, user ratings, and artists
        with open(genrePickle, "rb") as file:
            self.genreLE = pickle.load(file)

        with open(songPickle, "rb") as file:
            self.songLE = pickle.load(file)

        with open(artistPickle, "rb") as file:
            self.artistLE = pickle.load(file)

        # Map the human understandable information to what the network understands
        self.trainTestValDataFrame["songIndex"] = self.songLE.transform(self.trainTestValDataFrame.song_mbid)
        self.trainTestValDataFrame["artistIndex"] = self.artistLE.transform(self.trainTestValDataFrame.artist_mbid)

        # Tensorize the pickled information to insert into the network
        self.songIndex = torch.tensor(self.trainTestValDataFrame.songIndex.values, dtype=torch.long)
        self.artistIndex = torch.tensor(self.trainTestValDataFrame.artistIndex.values, dtype=torch.long)
        self.playcounts = torch.tensor(self.trainTestValDataFrame.playcount.values, dtype=torch.float)
        self.listeners = torch.tensor(self.trainTestValDataFrame.listeners.values, dtype=torch.float)
        genreColumns = list(self.genreLE.classes_)
        self.genreValues = torch.tensor(self.trainTestValDataFrame[genreColumns].values, dtype=torch.float)
        

    # Get length of dataset
    def __len__(self):
        return len(self.songIndex)
    
    # Get a specific song/artist
    def __getitem__(self, idx):
        return (
            self.songIndex[idx],
            self.artistIndex[idx],
            self.playcounts[idx],
            self.listeners[idx],
            self.genreValues[idx]
        )