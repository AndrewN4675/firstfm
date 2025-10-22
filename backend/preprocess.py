### NOTE: Most of this code is based on JohnnyBoiTime's Movie NN code! Props to him

import pandas as pd
import os
import pickle
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
import json
import xml.etree.ElementTree as ET

# ----- File Location Constants -----
FI_ARTISTS = "../artist_top_tracks.json"
FI_TAGS = "../track_tags.json"
FO_COMB_XML = "combined_data.xml"
FO_GBA = "genres_by_artist.csv"
FO_GBS = "genres_by_song.csv"
FO_ARTIST_PKL = "artist_ids.pkl"
FO_SONG_PKL = "song_ids.pkl"
FO_GBA_PKL = "genres_by_artist.pkl"
FO_GBS_PKL = "genres_by_song.pkl"

# ----- Preprocessing Behavior Constants (Change these to tune results) -----
GENRES = ["pop", "rock", "rap", "indie", "Hip-Hop", "rnb", "alternative", "trap", "alternative rock", "k-pop",
          "indie rock", "electronic", "hip hop", "indie pop", "dance", "soul", "dream pop", "electropop", "classic rock", "pop rap",
          "metal", "folk", "Kpop", "synthpop", "pop rock", "alternative metal", "Nu Metal", "Neo-Soul", "emo", "new wave",
          "cloud rap", "hard rock", "shoegaze", "rage", "Grunge", "indie folk", "punk rock", "post-hardcore", "House", "funk",
          "Gangsta Rap", "dance-pop", "art pop", "alt-pop", "Reggaeton", "pop punk", "punk", "Disco", "country", "soft rock",
          "emo rap", "jazz", "metalcore", "Neo-Psychedelia", "post-punk", "heavy metal", "Progressive rock", "hyperpop"]  # top 60 genres (not tags)
TOP_N_GENRES = len(GENRES)  # limit number of genres?
GENRE_THRESHOLD = 15  # what minimum rating (from last.fm) makes a song/artist count as that genre?
SHOULD_REMOVE_NULLS = True  # should songs/artists not matching any genres be removed?

# ----- File management -----

def remove_old_output_files() -> None:
    # [REMOVE FOR FUTURE FEATURE]
    # old combined xml
    if os.path.exists(FO_COMB_XML):
        os.remove(FO_COMB_XML)

    # artists output csv
    if os.path.exists(FO_GBA):
        os.remove(FO_GBA)
    
    # songs output csv
    if os.path.exists(FO_GBS):
        os.remove(FO_GBS)

    # artist id pkl
    if os.path.exists(FO_ARTIST_PKL):
        os.remove(FO_ARTIST_PKL)

    # song id pkl
    if os.path.exists(FO_SONG_PKL):
        os.remove(FO_SONG_PKL)

    # genre-by-artist pkl
    if os.path.exists(FO_GBA_PKL):
        os.remove(FO_GBA_PKL)

    # genre-by-song pkl
    if os.path.exists(FO_GBS_PKL):
        os.remove(FO_GBS_PKL)

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

# ----- XML/CSV structure building & manipulating -----

def build_combined_xml(artists_json: dict, tags_json: dict) -> ET.ElementTree:
    # create xml object, we'll sort by songs
    # and get artist data later
    root = ET.Element("songs")

    # Add songs:
    # get list of artists, and the list of songs for said artist
    for artist, tracks in artists_json.items():
        # for each track for said artist, create an object and add data
        for track in tracks:
            song_elem = ET.SubElement(root, "song", name=track["name"])
            ET.SubElement(song_elem, "playcount").text = track["playcount"]
            ET.SubElement(song_elem, "listeners").text = track["listeners"]
            ET.SubElement(song_elem, "mbid").text = track.get("mbid", "")
            ET.SubElement(song_elem, "url").text = track["url"]
            ET.SubElement(song_elem, "artist").text = artist
    
    # Add tags to those songs
    # Index songs for fast lookup by artist + song name
    songs_index = {}
    for song_elem in root.findall("song"):
        # song name attr is unique only within artist, so we need artist text inside song elem to key map
        key = (song_elem.find("artist").text, song_elem.attrib["name"])
        songs_index[key] = song_elem
    
    # get list of artists, and the list of songs for said artist
    for artist, tracks_dict in tags_json.items():
        # get each song and said song's list of tags
        for song_name, tags in tracks_dict.items():
            key = (artist, song_name)
            if key in songs_index:
                song_elem = songs_index[key]  # get song element
                tags_elem = ET.SubElement(song_elem, "tags")  # crate tag element
                for tag in tags:
                    tag_elem = ET.SubElement(tags_elem, "tag", count=str(tag["count"]))  # add specific tag to list with count
                    tag_elem.text = tag["name"]  # set name of object
    
    tree: ET.ElementTree = ET.ElementTree(root)

    return tree

def genre_by_song_csv(xml_tree, genre_list, genre_threshold) -> pd.DataFrame:
    root = xml_tree.getroot()
    genres_lower = [g.lower() for g in genre_list]

    song_data = []
    for song in root.findall("song"):
        song_name = song.get("name")

        # Initialize genre flags as 0
        genre_flags = dict.fromkeys(genres_lower, 0)

        tags_elem = song.find("tags")
        if tags_elem is not None:
            for tag in tags_elem.findall("tag"):
                tag_name = tag.text.lower()
                tag_count = int(tag.attrib.get("count", "0"))
                if tag_name in genre_flags and tag_count > genre_threshold:
                    genre_flags[tag_name] = 1

        row = {"song": song_name}
        row.update(genre_flags)
        song_data.append(row)

    df_songs = pd.DataFrame(song_data)
    return df_songs

def genre_by_artist_csv(xml_tree, genre_list, genre_threshold) -> pd.DataFrame:
    root = xml_tree.getroot()
    genres_lower = [g.lower() for g in genre_list]

    # Collect all songs per artist and accumulate genre counts
    artist_genre_counts = {}

    # Count number of songs per artist
    artist_song_counts = {}

    for song in root.findall("song"):
        artist_name = song.findtext("artist")
        artist_song_counts[artist_name] = artist_song_counts.get(artist_name, 0) + 1

    # Initialize artist genre counts dict
    for artist in artist_song_counts:
        artist_genre_counts[artist] = dict.fromkeys(genres_lower, 0)

    # Accumulate genre counts per artist across their songs
    for song in root.findall("song"):
        artist_name = song.findtext("artist")
        tags_elem = song.find("tags")
        if tags_elem is None:
            continue

        for tag in tags_elem.findall("tag"):
            tag_name = tag.text.lower()
            tag_count = int(tag.attrib.get("count", "0"))

            if tag_name in genres_lower:
                artist_genre_counts[artist_name][tag_name] += tag_count

    # Now create rows applying threshold scaled by # songs of artist
    artist_data = []
    for artist, genre_counts in artist_genre_counts.items():
        scaled_threshold = genre_threshold * artist_song_counts[artist]
        genre_flags = {g: int(count > scaled_threshold) for g, count in genre_counts.items()}

        row = {"artist": artist}
        row.update(genre_flags)
        artist_data.append(row)

    df_artists = pd.DataFrame(artist_data)
    return df_artists

# ----- Preprocessing -----

def remove_unaccepted_tags(xml_tree):
    """
    Remove <tag> elements from songs or artists not in GENRES.
    is_artist=True to process artist tags, False for song tags.
    """
    root = xml_tree.getroot()
    accepted = set(g.lower() for g in GENRES)

    # Choose elements to process
    elements = root.findall(".//song")

    for elem in elements:
        tags = elem.find("tags")
        if tags is None:
            continue
        for tag in list(tags):
            tag_name = tag.text.lower()
            if tag_name not in accepted:
                tags.remove(tag)

def remove_null_song_genres(xml_tree):
    """
    Process songs to:
     1. Remove tags with count <= GENRE_THRESHOLD.
     2. Remove songs with no <tags> element.
     3. Remove songs with 0 tags after filtering.
    """
    
    if not SHOULD_REMOVE_NULLS:
        return
    
    root = xml_tree.getroot()

    for song in list(root.findall("song")):
        tags_elem = song.find("tags")

        # Step 2: remove songs with no tags element
        if tags_elem is None:
            root.remove(song)
            continue

        # Step 1: remove tags with count <= GENRE_THRESHOLD
        for tag in list(tags_elem.findall("tag")):
            count = int(tag.attrib.get("count", 0))
            if count <= GENRE_THRESHOLD:
                tags_elem.remove(tag)

        # Step 3: remove songs with zero remaining tags
        if len(tags_elem.findall("tag")) == 0:
            root.remove(song)

# ----- Binarization and Encoding ------

# ----- Main -----

def main():
    print("----- Starting Preprocessing... -----")

    # 1.  remove old output files if they exist
    print("--> [0/12] Removing old output files...")
    remove_old_output_files()

    # 2.  read artist and tracks into json
    print("--> [1/12] Reading artist songs and track tags from json files...")
    artist_tracks_json = read_json(FI_ARTISTS)
    track_tags_json = read_json(FI_TAGS)

    # 3.  combine data from artist's songs and their tags into one xml
    print("--> [2/12] Combining data into one xml tree...")
    combined_xml: ET.ElementTree = build_combined_xml(artist_tracks_json, track_tags_json)

    # [TODO]: Add label encoders to xml as well, for future-proofing data?

    # 4.  Apply preprocessing strategies to data
    print("--> [3/12] Applying preprocessing strategies to data to clean...")
    remove_unaccepted_tags(combined_xml)
    remove_null_song_genres(combined_xml)

    # 5.  create a pandas dataframe for genre by song
    print("--> [4/12] Creating DataFrame for genre-by-song...")
    df_song = genre_by_song_csv(combined_xml, GENRES, GENRE_THRESHOLD)

    # 6.  create a pandas df for genre by artist
    print("--> [5/12] Creating DataFrame for genre-by-artist...")
    df_artist = genre_by_artist_csv(combined_xml, GENRES, GENRE_THRESHOLD)

    # 7. LabelEncode song names
    print("--> [6/12] Encoding song labels...")
    song_encoder = LabelEncoder()
    df_song["song_id"] = song_encoder.fit_transform(df_song["song"])  # Assume df_song (cols: "song", genre columns...)

    # 8. LabelEncode artist names
    print("--> [7/12] Encoding artist labels...")
    artist_encoder = LabelEncoder()
    df_artist["artist_id"] = artist_encoder.fit_transform(df_artist["artist"])  # Assume df_song ("artist", genre columns...)

    # 9. Prepare genre columns list (exclude name/id)
    print("--> [8/12] Preparing df's for binarizing...")
    song_genre_cols = df_song.columns.difference(["song", "song_id"])
    artist_genre_cols = df_artist.columns.difference(["artist", "artist_id"])

    # 10. Create MultiLabelBinarizer for songs
    print("--> [9/12] Creating MultiLabelBinarizer (matrix of 1's and 0's) for genre-by-song...")
    song_genre_lists = [
        [genre for genre in song_genre_cols if row[genre] == 1]
        for idx, row in df_song.iterrows()
    ]
    mlb_songs = MultiLabelBinarizer()
    song_genre_matrix = mlb_songs.fit_transform(song_genre_lists)

    # 11. Create MultiLabelBinarizer for artists
    print("--> [10/12] Creating MultiLabelBinarizer (matrix of 1's and 0's) for genre-by-artist...")
    artist_genre_lists = [
        [genre for genre in artist_genre_cols if row[genre] == 1]
        for idx, row in df_artist.iterrows()
    ]
    mlb_artists = MultiLabelBinarizer()
    artist_genre_matrix = mlb_artists.fit_transform(artist_genre_lists)

    # 12. Write out pkl's, csv's, and combined xml
    print("--> [11/12] Writing output files...")
    write_pkl(song_genre_matrix, FO_GBS_PKL)
    write_pkl(artist_genre_matrix, FO_GBA_PKL)

    write_csv(df_song, FO_GBS)
    write_csv(df_artist, FO_GBA)

    combined_xml.write(FO_COMB_XML, encoding="utf-8", xml_declaration=True)

    print("--> [12/12] Done!")

if __name__ == "__main__":
    main()
