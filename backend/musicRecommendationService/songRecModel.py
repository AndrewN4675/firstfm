import torch
import pickle
import pandas as pd
import numpy as np
import os
from pathlib import Path
import torch.nn.functional as F
from musicModel.model import ArtistSongRecModel

# File paths
currentDirectory = os.path.dirname(os.path.abspath(__file__))
projectRoot = os.path.abspath(os.path.join(currentDirectory, os.pardir))
backendDir = Path(__file__).resolve().parent.parent
songsDirectory = backendDir / "proccsedData" / "songs"
songCSV = songsDirectory / "genre_by_song.csv"
songsArtistsNames = songsDirectory / "song_artist_mbid_genre.csv"
songs = pd.read_csv(songCSV)
mbidToSongArtistName = pd.read_csv(songsArtistsNames)
songPickle   = os.path.join(projectRoot, "proccsedData", "pickles", "song_labels.pkl")
artistPickle = os.path.join(projectRoot, "proccsedData", "pickles", "artist_labels.pkl")
genrePickle  = os.path.join(projectRoot, "proccsedData", "pickles", "genre_labels.pkl")
songIDToTitle = dict(zip(mbidToSongArtistName.song_mbid, mbidToSongArtistName.song_name))
titleToSongID = dict(zip(mbidToSongArtistName.song_name, mbidToSongArtistName.song_mbid))
songIdToArtist = dict(zip(mbidToSongArtistName.song_mbid, mbidToSongArtistName.artist_name))


# Path to model
trainedModel = os.path.join(projectRoot, "musicModel", "models", "movierec.pth")


# Load info for information retrieval
with open(songPickle, "rb") as f:
    songEncoder = pickle.load(f)

with open(genrePickle, "rb") as f:
    genreLE = pickle.load(f)

# Form the genre matrix 
non_genre_cols = {
    "song_mbid","artist_mbid","playcount","listeners",
    "song_enc_id","artist_enc_id"
}
genre_cols = [c for c in songs.columns if c not in non_genre_cols]
numSongs = len(songEncoder.classes_)
genres = len(genre_cols)
genresMatrix = np.zeros((numSongs, genres))
enc_ids     = songs["song_enc_id"].to_numpy(dtype=int)
genre_block = songs[genre_cols].to_numpy(dtype=np.float32)
genresMatrix[enc_ids] = genre_block
genreTensor = torch.from_numpy(genresMatrix) 

# Get all the song id's from the song encoder
classes = songEncoder.classes_  
indexToSongMBID = {i: classes[i] for i in range(len(classes))} 


# Load the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ArtistSongRecModel(
    numSongs=4934, numArtists=1055, numGenres=58,
    songArtistEmbedSize=32, genreEmbedSize=8, HLSize=64
).to(device)

state = torch.load(trainedModel, map_location=device)
model.load_state_dict(state)
model.eval()


songEmbedds = model.songEmbedding.weight.detach().cpu()
songEmbedds = F.normalize(songEmbedds, dim=1)


def musicRecommendationSystem(songName: str, k: int = 5):

    # Convert the song name to the mbid so we can just
    # put in th song title
    song_mbid = titleToSongID[songName]

    # Make sure the mbid exists in the encoder
    try:
        index = int(songEncoder.transform([song_mbid])[0])
    except Exception:
        raise KeyError(f"Song MBID {song_mbid} not found in encoder")   

    # Finds the similar songs to the inputted one 
    queryVector = songEmbedds[index].unsqueeze(0).to(device)
    calcSimilarity = F.cosine_similarity(queryVector, songEmbedds.to(device))
    calcSimilarity[index] = -1.0               
    genreQuery = genreTensor[index]              
    overlappingGenres = (genreTensor * genreQuery).sum(dim=1)  
    sharedMask = overlappingGenres >= 2
    calcSimilarity[~sharedMask] = -1.0  
    topVals, topIdx = torch.topk(calcSimilarity, k) 
    
    # Make display all of the movies!
    return [
        (songIDToTitle.get(indexToSongMBID[i.item()]), songIdToArtist.get(indexToSongMBID[i.item()]), topVals[j].item())
        for j, i in enumerate(topIdx)
    ]