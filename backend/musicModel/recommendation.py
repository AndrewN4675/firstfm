import torch
import pickle
import pandas as pd
import numpy as np
import os
from pathlib import Path
import torch.nn.functional as F
from model import ArtistSongRecModel


"""
# --- paths ---
currentDirectory = os.path.dirname(os.path.abspath(__file__))
projectRoot = os.path.abspath(os.path.join(currentDirectory, os.pardir))
backendDir = Path(__file__).resolve().parent.parent
songsDirectory = backendDir / "proccsedData" / "songs"

songPickle   = os.path.join(projectRoot, "proccsedData", "pickles", "song_labels.pkl")
artistPickle = os.path.join(projectRoot, "proccsedData", "pickles", "artist_labels.pkl")
genrePickle  = os.path.join(projectRoot, "proccsedData", "pickles", "genre_labels.pkl")

trainedModel = os.path.join(projectRoot, "musicModel", "models", "movierec.pth")

# --- label encoder: MBID <-> index ---
with open(songPickle, "rb") as f:
    songEncoder = pickle.load(f)

classes = songEncoder.classes_  # np.array of MBIDs; index i corresponds to embedding row i
indexToSongMBID = {i: classes[i] for i in range(len(classes))}  # optional lookup

# --- model ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ArtistSongRecModel(
    numSongs=4934, numArtists=1055, numGenres=58,
    songArtistEmbedSize=32, genreEmbedSize=8, HLSize=64
).to(device)

state = torch.load(trainedModel, map_location=device)
model.load_state_dict(state)
model.eval()

# get normalized song embeddings
with torch.no_grad():
    # Adjust attribute name if your model uses a different one (e.g., model.song_emb)
    songEmbeds = model.songEmbedding.weight.detach().cpu()
    songEmbeds = F.normalize(songEmbeds, dim=1)  # cosine-friendly

def recommendationSystemTest(song_mbid: str, k: int = 5):
    Return top-k similar songs by MBID using cosine similarity in embedding space.
    # Get the encoder index for this MBID
    try:
        idx = int(songEncoder.transform([song_mbid])[0])
    except Exception:
        raise KeyError(f"MBID not found in encoder: {song_mbid}")

    with torch.no_grad():
        q = songEmbeds[idx].unsqueeze(0)                        # (1, d)
        sims = F.cosine_similarity(q, songEmbeds, dim=1)        # (N,)
        sims[idx] = -1.0                                        # exclude the query itself
        top_vals, top_idx = torch.topk(sims, k)

    # map back to MBIDs
    recs = [(indexToSongMBID[i.item()], float(top_vals[j].item())) for j, i in enumerate(top_idx)]
    return recs

"""

# Create paths to files
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


def recommendationSystemTest(songName: str, k: int = 5):

    # Convert the song name to the mbid so we can just
    # put in th song title
    song_mbid = titleToSongID[songName]

    # Make sure the mbid exists in the encoder
    try:
        index = int(songEncoder.transform([song_mbid])[0])
    except Exception:
        raise KeyError(f"Song MBID {song_mbid} not found in encoder")   

    # Calculate the similarity and find the top songs similar to the inputted,
    # based on what the network determines to be "similar"
    queryVector = songEmbedds[index].unsqueeze(0).to(device)
    calcSimilarity = F.cosine_similarity(queryVector, songEmbedds.to(device))
    calcSimilarity[index] = -1.0               
    genreQuery = genreTensor[index]              
    overlappingGenres = (genreTensor * genreQuery).sum(dim=1)  
    sharedMask = overlappingGenres >= 2
    calcSimilarity[~sharedMask] = -1.0  
    topVals, topIdx = torch.topk(calcSimilarity, k) 
    
    # Map the songID to its respective song title and genre
    return [
        (songIDToTitle.get(indexToSongMBID[i.item()]), songIdToArtist.get(indexToSongMBID[i.item()]), topVals[j].item())
        for j, i in enumerate(topIdx)
    ]