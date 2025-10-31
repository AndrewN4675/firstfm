### NOTE: Most of this code is based on JohnnyBoiTime's Movie NN code! Props to him

import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
import json
import xml.etree.ElementTree as ET
from tqdm import tqdm
from time import sleep
from dataclasses import dataclass, field
from typing import List, Tuple, Set, MutableMapping, Union

# ----- File Location Constants -----
FI_ARTISTS = "../artist_top_tracks.json"
FI_TAGS = "../track_tags.json"
FO_COMB_XML = "combined_data.xml"
FO_GBA = "genre_by_artist"
FO_GBS = "genre_by_song"
FO_ARTIST_ENC = "artist_labels.pkl"
FO_SONG_ENC = "song_labels.pkl"
FO_GENRE_ENC = "genre_labels.pkl"

# ----- Preprocessing Behavior Constants (Change these to tune results) -----
GENRES = ["pop", "rock", "rap", "indie", "Hip-Hop", "rnb", "alternative", "trap", "alternative rock", "k-pop",
          "indie rock", "electronic", "hip hop", "indie pop", "dance", "soul", "dream pop", "electropop", "classic rock", "pop rap",
          "metal", "folk", "Kpop", "synthpop", "pop rock", "alternative metal", "Nu Metal", "Neo-Soul", "emo", "new wave",
          "cloud rap", "hard rock", "shoegaze", "rage", "Grunge", "indie folk", "punk rock", "post-hardcore", "House", "funk",
          "Gangsta Rap", "dance-pop", "art pop", "alt-pop", "Reggaeton", "pop punk", "punk", "Disco", "country", "soft rock",
          "emo rap", "jazz", "metalcore", "Neo-Psychedelia", "post-punk", "heavy metal", "Progressive rock", "hyperpop"]  # top 60 genres (not tags)
TOP_N_GENRES = len(GENRES)  # limit number of genres?
GENRES = GENRES[:TOP_N_GENRES]  # truncate list based on TOP_N_GENRES
GENRES = sorted(GENRES, key=str.lower)  # sort list for later encoding
GENRE_THRESHOLD = 15  # what minimum rating (from last.fm) makes a song/artist count as that genre?
NORMALIZE_ARTIST_GENRE_COUNT: bool = True
REMOVE_GENRES_BELOW_THRESHOLD: bool = True
REMOVE_NO_GENRE_ARTISTS: bool = True
REMOVE_NO_GENRE_SONGS: bool = True
SONG_COLUMNS = ["song_mbid", "artist_mbid", "playcount", "listeners", "[GENRES ...]", "song_enc_id", "artist_enc_id"]
ARTIST_COLUMNS = "artist_mbid", "total_playcount", "total_listeners", "[GENRES ...]", "artist_enc_id"

# ----- Dataclasses -----

@dataclass
class Genre:
    name: str
    count: int = 0

@dataclass
class Artist:
    mbid: str
    name: str
    songs: int = 0
    total_playcount: int = 0
    total_listeners: int = 0
    genres: dict[str, Genre] = field(default_factory=dict)
    encoded_id: int = 0

@dataclass
class Song:
    mbid: str
    name: str
    artist_mbid: str
    artist_name: str
    playcount: int = 0
    listeners: int = 0
    genres: dict[str, Genre] = field(default_factory=dict)
    encoded_id: int = 0

# ----- File management -----

def read_json(filename: str) -> dict:
    with open(filename, "r", encoding='utf-8') as f:
        return json.load(f)

def write_pkl(data, filename) -> None:
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def write_csv(data: pd.DataFrame, csv_filename: str, pkl_filename: str = "") -> None:
    data.to_csv(csv_filename, index=False)

    if pkl_filename:
        write_pkl(data, pkl_filename)

# ----- Data Processing -----

def combine_data(artist_tracks_json: dict, track_tags_json: dict) -> Tuple[dict[str, Artist], dict[str, Song]]:
    artists = dict[str, Artist]()
    songs = dict[str, Song]()

    def tryGetStr(data: dict, entry: str, default: str):
        try:
            return data[entry]
        except KeyError:
            return default
        
    # get general data about artists and songs-- sans genre or encoding
    print("\n--> Making a list of all artists and songs...")
    pbar = tqdm(total=len(artist_tracks_json.items()))

    for artist, tracks in artist_tracks_json.items():
        artist = Artist(tryGetStr(tracks[0]["artist"], "mbid", "N/A"), artist)

        for track in tracks:
            # get data about this song
            song = Song(
                mbid = tryGetStr(track, "mbid", ""),
                name = tryGetStr(track, "name", ""),
                artist_name = artist.name,
                artist_mbid = artist.mbid,
                playcount = int(tryGetStr(track, "playcount", "0")),
                listeners = int(tryGetStr(track, "listeners", "0")),
                # genres filled later
                # encoded id entered later
            )

            # add this song to the list of all songs
            songs[song.name] = song

            # add data about this song to the artist object
            artist.songs += 1
            artist.total_playcount += song.playcount
            artist.total_listeners += song.listeners
        
        # add artist to the list of all artists
        artists[artist.name] = artist
        
        # update progress bar with next artist
        pbar.update(1)
    pbar.close()
    
    # now compile information about genres into songs
    print("\n--> Collecting information about each song's genre...")
    pbar = tqdm(total=len(songs))

    for artist, tracks in track_tags_json.items():
        for song_name, tags in tracks.items():
            if song_name in songs:
                for tag in tags:
                    genre = Genre(name=tag["name"], count=tag["count"])
                    songs[song_name].genres[genre.name] = genre
            
            pbar.update(1)
    
    songs_wo_tags = len(songs) - pbar.n
    pbar.update(songs_wo_tags)
    pbar.close()

    # now compile information about genres into artists
    print("\n--> Collecting information about each artist's genres...")
    pbar = tqdm(total=len(songs))

    for song in songs.values():
        for genre in song.genres.values():
            if genre.name in artists[song.artist_name].genres:
                artists[song.artist_name].genres[genre.name].count += genre.count
            else:
                artists[song.artist_name].genres[genre.name] = genre
        
        pbar.update(1)

    pbar.close()

    print(f"\nTotal # Songs: {len(songs)}")
    print(f"Total # Artists: {len(artists)}")
    print(f"Total Songs w/o tags: {songs_wo_tags}")

    return (artists, songs)

# ----- Data Preprocessing -----

def normalize_artist_genre_counts(artists: dict[str, Artist]) -> None:
    print("\n--> Normalizing artist genre counts...")
    pbar = tqdm(total=len(artists))

    for artist in artists.values():
        # get top genre
        genre_counts = [genre.count for genre in artist.genres.values()]
        top_genre_count = max(genre_counts) if len(genre_counts) > 0 else 100

        # normalize genre counts to 0 <= count <= 100
        for genre in artist.genres.values():
            genre.count = int((genre.count / top_genre_count) * 100)
        
        pbar.update(1)
    
    pbar.close()

def remove_below_threshold_genres(artists: dict[str, Artist], songs: dict[str, Song]) -> None:
    # artists
    print("\n--> Removing artist's genres below threshold...")
    pbar = tqdm(total=len(artists))

    for artist in artists.values():
        genres_to_remove = []
        
        for genre in artist.genres.values():
            if genre.count < GENRE_THRESHOLD:
                genres_to_remove.append(genre.name)
        
        for genre in genres_to_remove:
            artist.genres.pop(genre)

        pbar.update(1)
    
    pbar.close()

    # songs
    print("\n--> Removing song's genres below threshold...")
    pbar = tqdm(total=len(songs))

    for song in songs.values():
        genres_to_remove = []
        
        for genre in song.genres.values():
            if genre.count < GENRE_THRESHOLD:
                genres_to_remove.append(genre.name)
        
        for genre in genres_to_remove:
            song.genres.pop(genre)

        pbar.update(1)
    
    pbar.close()

# ----- Main -----

def main():
    print("----- Starting Preprocessing... -----")

    # read jsons for artist songs and song tags
    artist_tracks_json: dict = read_json(FI_ARTISTS)
    track_tags_json: dict = read_json(FI_TAGS)

    # Combine data into two lists
    artists, songs = combine_data(artist_tracks_json, track_tags_json)

    # Preprocess the data
    if NORMALIZE_ARTIST_GENRE_COUNT: normalize_artist_genre_counts(artists)
    if REMOVE_GENRES_BELOW_THRESHOLD: remove_below_threshold_genres(artists, songs)

    print(artists["Tyler, The Creator"])
    print(songs["Throne"])

if __name__ == "__main__":
    main()
