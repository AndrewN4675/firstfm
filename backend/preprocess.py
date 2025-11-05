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
import numpy as np

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
GENRES = sorted(GENRES)  # sort list for later encoding
GENRE_THRESHOLD = 15  # what minimum rating (from last.fm) makes a song/artist count as that genre?
REMOVE_NO_GENRE_SONGS: bool = True
REMOVE_NO_GENRE_ARTISTS: bool = True
REMOVE_NA_MBID_ARTISTS: bool = True
REMOVE_NA_MBID_SONGS: bool = True
NORMALIZE_ARTIST_GENRE_COUNT: bool = True
NA_VAL = "N/A"

# ----- Dataclasses -----

@dataclass
class Genre:
    name: str
    count: int = 0

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

@dataclass
class Artist:
    mbid: str
    name: str
    total_playcount: int = 0
    total_listeners: int = 0
    genres: dict[str, Genre] = field(default_factory=dict)
    songs: dict[str, Song] = field(default_factory=dict)
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

def combine_data(artist_tracks_json: dict, track_tags_json: dict) -> dict[str, Artist]:
    artists = dict[str, Artist]()  # artists keyed by their mbid

    def tryGetStr(data: dict, entry: str, default: str):
        try:
            return data[entry]
        except KeyError:
            return default
        
    # collect a list of artists and their songs
    print("\n--> Making a list of all artists and songs...")
    pbar = tqdm(total=len(artist_tracks_json.items()))

    for artist, tracks in artist_tracks_json.items():
        artist = Artist(tryGetStr(tracks[0]["artist"], "mbid", NA_VAL), artist)

        for track in tracks:
            # get data about this song
            song = Song(
                mbid = tryGetStr(track, "mbid", NA_VAL),
                name = tryGetStr(track, "name", NA_VAL),
                artist_name = artist.name,
                artist_mbid = artist.mbid,
                playcount = int(tryGetStr(track, "playcount", "0")),
                listeners = int(tryGetStr(track, "listeners", "0")),
                # genres filled later
                # encoded id entered later
            )

            # add this song to the list of artist's songs
            artist.songs[song.name] = song

            # add data about this song to the artist object
            artist.total_playcount += song.playcount
            artist.total_listeners += song.listeners
        
        # add artist to the list of all artists
        artists[artist.name] = artist
        
        # update progress bar with next artist
        pbar.update(1)
    pbar.close()

    # now compile information about genres into songs
    print("\n--> Collecting information about each song's genre...")
    total_songs = sum([len(artist.songs) for artist in artists.values()])
    pbar = tqdm(total=total_songs)

    for artist, tracks in track_tags_json.items():
        for song_name, tags in tracks.items():
            if song_name in artists[artist].songs:
                for tag in tags:
                    genre = Genre(name=tag["name"], count=tag["count"])
                    artists[artist].songs[song_name].genres[genre.name] = genre
            
            pbar.update(1)
    
    songs_wo_tags = total_songs - pbar.n
    pbar.update(songs_wo_tags)
    pbar.close()

    return artists

def total_artist_genres(artists: dict[str, Artist]) -> None:
    # compile information about genres into artists
    print("\n--> Collecting information about each artist's genres...")
    pbar = tqdm(total=len(artists))

    for artist in artists.values():
        for song in artist.songs.values():
            for genre in song.genres.values():
                if genre.name in artist.genres:
                    artist.genres[genre.name].count += genre.count
                else:
                    artist.genres[genre.name] = genre
        
        pbar.update(1)

    pbar.close()

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

def remove_no_genre_songs(artists: dict[str, Artist]) -> None:
    print("\n--> Finding songs with no genres listed...")
    pbar = tqdm(total=len(artists))

    # collect tuples of (artist_mbid, song_name)
    songs_to_remove: list[tuple[str, str]] = []

    for artist_mbid, artist in artists.items():
        for song_name, song in artist.songs.items():
            if not song.genres:
                songs_to_remove.append((artist_mbid, song_name))
        pbar.update(1)
    pbar.close()

    print(f"\n--> Removing {len(songs_to_remove)} songs with no genres listed...")
    pbar = tqdm(total=len(songs_to_remove))

    for artist_mbid, song_name in songs_to_remove:
        artist = artists.get(artist_mbid)
        if artist is None:
            pbar.update(1)
            continue
        # pop safely
        artist.songs.pop(song_name, None)
        pbar.update(1)
    pbar.close()

def remove_no_genre_artists(artists: dict[str, Artist]) -> None:
    print("\n--> Finding artists with no genres listed...")
    pbar = tqdm(total=len(artists))

    artists_to_remove = list[str]()

    for artist in artists.values():
        if len(artist.genres) == 0:
            artists_to_remove.append(artist.name)
        
        pbar.update(1)
    
    pbar.close()

    print("\n--> Removing artists with no genres listed...")
    pbar = tqdm(total=len(artists_to_remove))

    for artist in artists_to_remove:
        artists.pop(artist)
        pbar.update(1)
    
    pbar.close()

def remove_na_mbid_artists(artists: dict[str, Artist]) -> None:
    print("\n--> Finding artists with NA mbid...")
    pbar = tqdm(total=len(artists), desc="Scanning artists", unit="artist")

    to_remove: list[str] = []
    for mbid, artist in list(artists.items()):
        if mbid == NA_VAL or (hasattr(artist, "mbid") and artist.mbid == NA_VAL):
            to_remove.append(mbid)
        pbar.update(1)
    pbar.close()

    if not to_remove:
        print("  -> No NA-mbid artists found.")
        return

    print(f"\n--> Removing {len(to_remove)} artists with NA mbid...")
    pbar = tqdm(total=len(to_remove), desc="Removing artists", unit="artist")
    for mbid in to_remove:
        artists.pop(mbid, None)
        pbar.update(1)
    pbar.close()

def remove_na_mbid_songs(artists: dict[str, Artist], songs: dict[str, Song] | None = None) -> None:
    print("\n--> Finding songs with NA mbid...")
    # Count artists as progress target (we scan each artist)
    pbar = tqdm(total=len(artists), desc="Scanning artists", unit="artist")

    removals: dict[str, list[str]] = {}  # artist_mbid -> list of song keys to remove

    for artist_mbid, artist in artists.items():
        # collect song keys to remove for this artist
        to_remove_keys: list[str] = []
        for key, song in list(artist.songs.items()):
            # check song.mbid (and also key as fallback) against NA_VAL
            if (hasattr(song, "mbid") and song.mbid == NA_VAL) or key == NA_VAL:
                to_remove_keys.append(key)
        if to_remove_keys:
            removals[artist_mbid] = to_remove_keys
        pbar.update(1)
    pbar.close()

    total_removals = sum(len(v) for v in removals.values())
    if total_removals == 0:
        print("  -> No NA-mbid songs found.")
        return

    print(f"\n--> Removing {total_removals} songs with NA mbid...")
    pbar = tqdm(total=total_removals, desc="Removing songs", unit="song")

    for artist_mbid, keys in removals.items():
        artist = artists.get(artist_mbid)
        if artist is None:
            # artist may have been removed earlier; skip safely
            for _ in keys:
                pbar.update(1)
            continue

        for key in keys:
            # remove from artist.songs
            artist.songs.pop(key, None)
            # also remove from global songs dict if provided and if key or song.mbid present
            if songs is not None:
                # try by key first (common case if artist.songs keyed by song.mbid)
                songs.pop(key, None)
                # also attempt to remove by song.mbid if we have it
                # (we need to guard attribute access in case song object was popped)
                # We can attempt to remove by previously-stored song object if needed,
                # but safe approach is to ignore missing entries.
            pbar.update(1)

    pbar.close()

# ----- Binarization, Encoding, and Preparation for CSV'ing -----

def remove_unaccepted_tags(artists: dict[str, Artist]) -> None:
    print("\n--> Removing unaccepted tags from artists & their songs...")
    pbar = tqdm(total=len(artists))

    for artist in artists.values():
        for song in artist.songs.values():
            genres_to_remove = list[str]()

            for genre in song.genres.values():
                if genre.name not in GENRES:
                    genres_to_remove.append(genre.name)
            
            for genre in genres_to_remove:
                song.genres.pop(genre)
        
        pbar.update(1)
    
    pbar.close()

def encode_lexicographically(input_list: list[str]) -> LabelEncoder:
    encoder = LabelEncoder()

    encoder.fit_transform(input_list)

    return encoder

def create_genre_by_artist_df(artists: dict[str, Artist], artist_enc: LabelEncoder) -> pd.DataFrame:
    artist_data = []  # rows of artist data

    for artist in artists.values():
        # ensure genre count exists for each genre
        for genre in GENRES:
            if genre not in artist.genres.keys():
                artist.genres[genre] = Genre(genre, 0)

        # make flags (0 or 1) for genres, with columns in sorted order by genre name
        genre_flags = {genre: int(artist.genres[genre].count > GENRE_THRESHOLD) for genre in GENRES}

        # make row with known values
        row = {
            "artist_mbid": artist.mbid,
            "total_playcount": artist.total_playcount,
            "total_listeners": artist.total_listeners,
        }

        # add many columns of genres
        row.update(genre_flags)

        # add artist enc id at end
        row.update({"artist_enc_id": int(np.where(artist_enc.classes_ == artist.mbid)[0][0])})
        artist_data.append(row)

    # convert to pandas dataframe, sort by mbid, and return it  
    df_artists = pd.DataFrame(artist_data)
    df_artists.sort_values(by="artist_mbid", inplace=True)
    return df_artists

def create_genre_by_song_df(artists: dict[str, Artist], artist_enc: LabelEncoder, song_enc: LabelEncoder) -> pd.DataFrame:
    song_data = []

    for artist in artists.values():
        for song in artist.songs.values():
            # ensure each genre from global GENRES exists in song.genres
            for genre in GENRES:
                if genre not in song.genres:
                    song.genres[genre] = Genre(genre, 0)

            # binary flags: 1 if genre count > threshold, else 0
            genre_flags = {genre: int(song.genres[genre].count > GENRE_THRESHOLD)
                           for genre in GENRES}

            # base row
            row = {
                "song_mbid": song.mbid,
                "artist_mbid": song.artist_mbid,
                "playcount": int(song.playcount or 0),
                "listeners": int(song.listeners or 0),
            }

            row.update(genre_flags)

            # encoded ids (find index in encoder.classes_)
            # using np.where to match your artist function style
            # fallback to -1 if not found (shouldn't happen if encoders built consistently)
            try:
                song_idx = int(np.where(song_enc.classes_ == song.mbid)[0][0])
            except Exception:
                song_idx = -1

            try:
                artist_idx = int(np.where(artist_enc.classes_ == song.artist_mbid)[0][0])
            except Exception:
                artist_idx = -1

            row.update({
                "song_enc_id": song_idx,
                "artist_enc_id": artist_idx,
            })

            song_data.append(row)

    # convert to pandas dataframe, sort by mbid, and return it
    df_songs = pd.DataFrame(song_data)
    df_songs.sort_values(by="song_mbid", inplace=True)
    return df_songs

# ----- Splitting data -----

def split_train_val_test(df: pd.DataFrame, test_size=0.2, val_size=0.1, random_state=42
                        ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # (your existing function — kept for clarity)
    train_val_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    val_df, train_df = train_test_split(train_val_df, test_size=1 - val_size, random_state=random_state)
    # reset indexes (optional but recommended)
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def split_df_sets(df: pd.DataFrame, test_size=0.2, val_size=0.1, random_state=42
                 ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Wrapper: split df into train/val/test and return them with reset indices.
    """
    return split_train_val_test(df, test_size=test_size, val_size=val_size, random_state=random_state)


def split_df_without_genres(df: pd.DataFrame,
                            test_size=0.2,
                            val_size=0.1,
                            random_state=42
                           ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Drop genre columns, split the remaining dataframe, and return train/val/test.
    - genres: list of genre column names to drop. If None, uses global GENRES.
    """

    # Only drop genre cols that actually exist in the DataFrame
    genre_cols_to_drop = [g for g in GENRES if g in df.columns]
    df_no_genres = df.drop(columns=genre_cols_to_drop, errors="ignore")
    return split_train_val_test(df_no_genres, test_size=test_size, val_size=val_size,
                                random_state=random_state)

# ----- Main -----

def main():
    print("----- Starting Preprocessing... -----")

    # read jsons for artist songs and song tags
    artist_tracks_json: dict = read_json(FI_ARTISTS)
    track_tags_json: dict = read_json(FI_TAGS)

    # Combine data into two lists
    artists = combine_data(artist_tracks_json, track_tags_json)

    # Preprocess the data (semi specific order)
    if REMOVE_NA_MBID_ARTISTS: remove_na_mbid_artists(artists)
    if REMOVE_NA_MBID_SONGS: remove_na_mbid_songs(artists)
    remove_unaccepted_tags(artists)
    if REMOVE_NO_GENRE_SONGS: remove_no_genre_songs(artists)
    total_artist_genres(artists)
    if REMOVE_NO_GENRE_ARTISTS: remove_no_genre_artists(artists)
    if NORMALIZE_ARTIST_GENRE_COUNT: normalize_artist_genre_counts(artists)

    # label encode artists by their mbid (lexicographically by mbid (uuid) string)
    artist_enc = encode_lexicographically([artist.mbid for artist in artists.values()])
    song_enc = encode_lexicographically([song.mbid for artist in artists.values() for song in artist.songs.values()])
    genre_enc = encode_lexicographically(GENRES)

    # create a genre-by-artist dataframe
    artist_df = create_genre_by_artist_df(artists, artist_enc)

    # create a genre-by-artist dataframe
    song_df = create_genre_by_song_df(artists, artist_enc, song_enc)

    # write pkl's for encoders
    write_pkl(artist_enc, FO_ARTIST_ENC)
    write_pkl(song_enc, FO_SONG_ENC)
    write_pkl(genre_enc, FO_GENRE_ENC)

    # write full csv's for artist and song
    write_csv(artist_df, FO_GBA + ".csv")
    write_csv(song_df, FO_GBS + ".csv")

    # write split data for artists
    artist_train, artist_val, artist_test = split_df_sets(artist_df)
    write_csv(artist_train, FO_GBA + "_train.csv")
    write_csv(artist_val, FO_GBA + "_val.csv")
    write_csv(artist_test, FO_GBA + "_test.csv")

    # write split data for songs (WITH genres)
    song_train, song_val, song_test = split_df_sets(song_df)
    write_csv(song_train, FO_GBS + "_train.csv")
    write_csv(song_val, FO_GBS + "_val.csv")
    write_csv(song_test, FO_GBS + "_test.csv")

    # write split data for songs (with OUT genres)
    song_train_ng, song_val_ng, song_test_ng = split_df_without_genres(song_df)
    write_csv(song_train_ng, FO_GBS + "_train_no_genres.csv")
    write_csv(song_val_ng, FO_GBS + "_val_no_genres.csv")
    write_csv(song_test_ng, FO_GBS + "_test_no_genres.csv")

if __name__ == "__main__":
    main()
