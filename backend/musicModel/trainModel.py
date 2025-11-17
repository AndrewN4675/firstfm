import torch
import os
from pathlib import Path
from torch import nn, optim
from torch.utils.data import DataLoader
from datasets import TrainTestVal
from model import ArtistSongRecModel


def main(): 

    currentDirectory = os.path.dirname(os.path.abspath(__file__))

    projectRoot = os.path.abspath(os.path.join(currentDirectory, os.pardir))

    backendDir = Path(__file__).resolve().parent.parent

    songsDirectory = backendDir / "proccsedData"/ "songs"

    training = songsDirectory / "genre_by_song_train.csv"
    validation = songsDirectory / "genre_by_song_val.csv"
    testing = songsDirectory / "genre_by_song_test.csv"

    songPickle = os.path.join(projectRoot, "proccsedData", "pickles", "song_labels.pkl")
    artistPickle = os.path.join(projectRoot, "proccsedData", "pickles", "artist_labels.pkl")
    genrePickle = os.path.join(projectRoot, "proccsedData", "pickles", "genre_labels.pkl")

    # Create data sets from the csv's def __init__(self, trainValTestCSV, processedSongsCSV, songPickle, artistPickle, genrePickle):
    trainingDataset = TrainTestVal(training, 
                                    songPickle,
                                    artistPickle,
                                    genrePickle
                                    )
    validationDataset = TrainTestVal(validation, 
                                    songPickle,
                                    artistPickle,
                                    genrePickle
                                    )
    testDataset = TrainTestVal(testing, 
                                    songPickle,
                                    artistPickle,
                                    genrePickle
                                    )

    # Loads them up. Shuffle training for randomness, but we need validation and testing to be more concrete
    # and deterministic
    trainingLoader = DataLoader(trainingDataset, batch_size=512, shuffle=True, num_workers=4)
    validationLoader = DataLoader(validationDataset, batch_size=512, shuffle=False, num_workers=4)
    testingLoader = DataLoader(testDataset, batch_size=512, shuffle=False, num_workers=4)

    numSongsFound = len(trainingDataset.songLE.classes_)
    numArtistsFound = len(trainingDataset.artistLE.classes_)
    numGenresFound = len(trainingDataset.genreLE.classes_)

    print(numSongsFound, numArtistsFound, numGenresFound)

    # self, numSongs, numArtists, numGenres, songArtistEmbedSize, genreEmbedSize, HLSize
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # check if GPU is available
    model = ArtistSongRecModel(numSongs=numSongsFound, numArtists = numArtistsFound, numGenres = numGenresFound, songArtistEmbedSize=32, genreEmbedSize=8, HLSize=64).to(device) # train on GPU, default CPU

    # calc loss and also optimze using the learning rate, low learning rate for slower learning
    calcLoss = nn.MSELoss()
    optimizeNetwork = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)

    # How many times we want to go through the network
    numberEpochs = 10

    poisson = nn.PoissonNLLLoss(log_input=True, full=False, reduction="sum")

    # Go through the network!
    for epoch in range(1, numberEpochs + 1):

        # Train the model
        model.train()
        totalTrainingLoss = 0.0
        totalTrainingLossSquared = 0.0
        totalTrainingLossSquaredLog = 0.0
        totalTrainingLossRMSLE = 0.0
        # Put users, movies, and ratings through the network
        for songs, artists, playcounts, listeners, genres in trainingLoader:
            # Use GPU or CPU
            songs, artists, playcounts, listeners, genres = (
                songs.to(device),
                artists.to(device),
                playcounts.to(device).float(),
                listeners.to(device).float().clamp_min(1.0),
                genres.to(device).float(),
            )

            log_rate = model(songs, artists, genres)
            logMean = log_rate + torch.log(listeners)
            optimizeNetwork.zero_grad()
            loss = poisson(logMean, playcounts)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            optimizeNetwork.step()

            totalTrainingLoss += loss.item()

            predictions = torch.exp(logMean)
            totalTrainingLossSquared += torch.sum((predictions - playcounts) ** 2).item()
            totalTrainingLossSquaredLog += torch.sum(
                (torch.log1p(predictions) - torch.log1p(playcounts)) ** 2
            ).item()
            
            
            totalTrainingLossRMSLE = (totalTrainingLossSquaredLog / len(trainingDataset)) ** 0.5

                        

        """
            
            # Zero old gradients, take networks output,
            # then compute loss
            optimizeNetwork.zero_grad()
            output = model(songs, artists, genres)
            loss = calcLoss(output, playcounts)

            # Backward pass and configure weights
            loss.backward()

            nn.utils.clip_grad_norm_(model.parameters(), 5)
            
            optimizeNetwork.step()

            # Loss for the epoch
            totalTrainingLoss += loss.item() * songs.size(0)

        averageTrainingLoss = totalTrainingLoss / len(trainingDataset)
        trainingRMSE = averageTrainingLoss ** 0.5

        """

        """
        # Evaluate the model!
        model.eval()
        newTotalTrainingLoss = 0.0
        with torch.no_grad():
              for users, movies, ratings, genres in trainingLoader:
                 # Use GPU or CPU
                users, movies, ratings, genres = (
                    users.to(device),
                    movies.to(device),
                    ratings.to(device),
                    genres.to(device)
            )

                output = model(users, movies, genres)
                newTotalTrainingLoss += calcLoss(output, ratings).item() * users.size(0)
        
        # calc RMSE/how well our model memorizes the data set
        averageTrainingLoss = newTotalTrainingLoss / len(trainingDataset)
        trainingRMSE = averageTrainingLoss ** 0.5

        """
        model.eval()
        totalValidationLoss = 0.0
        totalValidationLossSquared = 0.0
        totalValidationLossSquaredLog = 0.0
        with torch.no_grad():
            # Put users, movies, and ratings through the network
            for songs, artists, playcounts, listeners, genres in validationLoader:
                # Use GPU or CPU
                songs, artists, playcounts, listeners, genres = (
                    songs.to(device),
                    artists.to(device),
                    playcounts.to(device).float(),
                    listeners.to(device).float(),
                    genres.to(device).float(),
                )

                logRate = model(songs, artists, genres)
                logMean = logRate + torch.log(listeners)
                predictions = torch.exp(logMean)
                totalValidationLoss += poisson(logMean, playcounts).item()
                totalValidationLossSquared += torch.sum((predictions - playcounts) ** 2).item()
                totalValidationLossSquaredLog += torch.sum(
                    (torch.log1p(predictions) - torch.log1p(playcounts)) ** 2
                ).item()
                
    
                averageValLoss = totalValidationLoss / len(validationDataset)
                validationRMSLE = (totalValidationLossSquaredLog / len(validationDataset)) ** 0.5

        print(f"Current epoch: {epoch} training RMSLE={totalTrainingLossRMSLE:.4f}, validation RMSLE={validationRMSLE:.4f}")

    # Now, we do testing!
    model.eval()
    totalTestingLoss = 0.0
    totalTestingLossSquared = 0.0
    totalTestingLossSquaredLog = 0.0
    with torch.no_grad():
        for songs, artists, playcounts, listeners, genres in testingLoader:
            # Use GPU or CPU
            songs, artists, playcounts, listeners, genres = (
                songs.to(device),
                artists.to(device),
                playcounts.to(device).float(),
                listeners.to(device).float(),
                genres.to(device).float(),
            )
            logRate = model(songs, artists, genres)
            logMean = logRate + torch.log(listeners)
            predictions = torch.exp(logMean)
            totalTestingLoss += poisson(logMean, playcounts).item()
            totalTestingLossSquared += torch.sum((predictions - playcounts) ** 2).item()
            totalTestingLossSquaredLog += torch.sum(
                (torch.log1p(predictions) - torch.log1p(playcounts)) ** 2
            ).item()
                
    
            averageTestLoss = totalTestingLoss / len(testDataset)
            testingRMSE = averageTestLoss ** 0.5
            testingRMSLE = (totalTestingLossSquaredLog / len(testDataset)) ** 0.5

    print(f"testing RMSE = {testingRMSE:.4f}, testing RMSLE = {testingRMSLE:.4f}")

    # Save the model to use!
    torch.save(model.state_dict(), "models/musicrec.pth")

    print(f"Finished!")

# Windows so yeah
if __name__ == "__main__":
    main()