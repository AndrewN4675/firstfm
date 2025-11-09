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

currentDirectory = os.path.dirname(os.path.abspath(__file__))
projectRoot = os.path.abspath(os.path.join(currentDirectory, os.pardir))
backendDir = Path(__file__).resolve().parent.parent
songsDirectory = backendDir / "proccsedData" / "songs"

songCSV = songsDirectory / "genre_by_song.csv"

songs = pd.read_csv(songCSV)

songPickle   = os.path.join(projectRoot, "proccsedData", "pickles", "song_labels.pkl")
artistPickle = os.path.join(projectRoot, "proccsedData", "pickles", "artist_labels.pkl")
genrePickle  = os.path.join(projectRoot, "proccsedData", "pickles", "genre_labels.pkl")

trainedModel = os.path.join(projectRoot, "musicModel", "models", "movierec.pth")

# --- label encoder: MBID <-> index ---
with open(songPickle, "rb") as f:
    songEncoder = pickle.load(f)

with open(genrePickle, "rb") as f:
    genreLE = pickle.load(f)

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

classes = songEncoder.classes_  
indexToSongMBID = {i: classes[i] for i in range(len(classes))} 


# --- model ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ArtistSongRecModel(
    numSongs=4934, numArtists=1055, numGenres=58,
    songArtistEmbedSize=32, genreEmbedSize=8, HLSize=64
).to(device)

state = torch.load(trainedModel, map_location=device)
model.load_state_dict(state)
model.eval()


# Adjust attribute name if your model uses a different one (e.g., model.song_emb)
songEmbedds = model.songEmbedding.weight.detach().cpu()
songEmbedds = F.normalize(songEmbedds, dim=1)  # cosine-friendly

def recommendationSystemTest(song_mbid: str, k: int = 5):

    try:
        index = int(songEncoder.transform([song_mbid])[0])
    except Exception:
        raise KeyError(f"Song MBID {song_mbid} not found in encoder")   
    # --- Cosine similarity between embeddings ---
    queryVector = songEmbedds[index].unsqueeze(0).to(device)
    calcSimilarity = F.cosine_similarity(queryVector, songEmbedds.to(device))
    calcSimilarity[index] = -1.0                 # optional: exclude the query itself   
    # --- Genre info ---
    genreQuery = genreTensor[index]              # shape [G]
    
    # --- Find genre overlap ---
    overlappingGenres = (genreTensor * genreQuery).sum(dim=1)   
    # --- Mask: require at least `numGenres` shared genres ---
    sharedMask = overlappingGenres >= 2
    calcSimilarity[~sharedMask] = -1.0  
    # --- Top-k recommendations ---
    topVals, topIdx = torch.topk(calcSimilarity, k) 
    # Return MBIDs (or titles if you have them mapped)
    return [
        (indexToSongMBID[i.item()], topVals[j].item())
        for j, i in enumerate(topIdx)
    ]



