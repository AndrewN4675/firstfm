import torch
import torch.nn as nn
import torch.nn.functional as F

# basic neural network model for music recommendations

# inherits attributes from nn.Module
class ArtistRecModel(nn.Module):
    def __init__(self, numSongs, numArtists, numGenres, songArtistEmbedSize, genreEmbedSize, HLSize): #, dropout=0.5):
        super().__init__() # initialize parent class attributes first
        
        # Embedding users + movies
        self.artistEmbedding = nn.Embedding(numArtists, songArtistEmbedSize)
        self.songEmbedding = nn.Embedding(numSongs, songArtistEmbedSize)

        # Embedding biases for the users and movies
        self.artistBias = nn.Embedding(numArtists, 1)
        self.songBias = nn.Embedding(numSongs, 1)
        self.bias = nn.Parameter(torch.zeros(1)) # Global bias

        # Constructing the network. Adjust if needed later
        self.genreLinear = nn.Linear(numGenres, genreEmbedSize)
        self.fullyConnectedLayer1 = nn.Linear(songArtistEmbedSize * 2 + genreEmbedSize, HLSize)
        self.fullyConnectedLayer2 = nn.Linear(HLSize, 1)
      #  self.drop = nn.Dropout(dropout)

    # forward pass
    # MH = multi hot
    def forward(self, songIDs, artistIDs, genreMH):

        # Look up the users, movies, and genres
        songEmbeds = self.songEmbedding(songIDs)
        artistEmbeds = self.artistEmbedding(artistIDs)
        genreEmbeds = F.relu(self.genreLinear(genreMH))

        # Get the biases
        songBias = self.songBias(songIDs).squeeze(1)
        artistBias = self.artistBias(artistIDs).squeeze(1)

        # Compute the dot product
        dotProduct = (songEmbeds * artistEmbeds).sum(dim = 1)

        # go through network! Learn from non linear interactions
        x = torch.cat([songEmbeds, artistEmbeds, genreEmbeds], dim=1)
        x = F.relu(self.fullyConnectedLayer1(x))
        multiLayerPerceptron = self.fullyConnectedLayer2(x).squeeze(1)


        # Return output 
        return dotProduct + multiLayerPerceptron + songBias + artistBias + self.bias