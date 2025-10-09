### NOTE: Most of this code is based on JohnnyBoiTime's Movie NN code! Props to him

import pandas as pd
import os
import pickle
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split

# Find where this script lies:
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
projectRoot = os.path.abspath(os.path.join(scriptDirectory, os.pardir))

# Find out where the raw data and processed data live
rawDataDirectory = os.path.join(projectRoot, "data", "rawData")
processedDataDirectory = os.path.join(projectRoot, "data", "processed")

# Load data sets from the ml csv
ratings = pd.read_csv(os.path.join(rawDataDirectory, "ratings.csv"))
moviesDataFrame = pd.read_csv(os.path.join(rawDataDirectory, "movies.csv"))
