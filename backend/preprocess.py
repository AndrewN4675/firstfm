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
SHOULD_REMOVE_NULLS = False  # should songs/artists not matching any genres be removed?

# ----- File management -----

def remove_old_output_files():
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

def write_pkl(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def write_csv(data: pd.DataFrame, csv_filename: str, pkl_filename: str = None):
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

def genre_by_song_df(xml_tree, accepted_genres=None):
    """Build genre-by-song DataFrame from XML.
    Columns: ['song', 'artist', genre1, genre2, ...]
    accepted_genres: list or set of genres to keep; if None, use all found."""
    
    root = xml_tree.getroot()
    # First pass: gather all song genre sets
    rows = []
    all_genres = set()

    for song_elem in root.findall("song"):
        song_name = song_elem.attrib.get("name")
        artist_name = song_elem.findtext("artist")
        tags_elem = song_elem.find("tags")
        genres = extract_genres_from_tags(tags_elem)
        
        # Filter to accepted genres if specified
        if accepted_genres:
            genres = {g: c for g, c in genres.items() if g in accepted_genres}

        all_genres.update(genres.keys())

        rows.append({
            "song": song_name,
            "artist": artist_name,
            "genres": genres
        })

    all_genres = sorted(all_genres)

    # Build DataFrame rows with multi-hot encoding of genres
    data = []
    for row in rows:
        genre_vector = [1 if g in row["genres"] and row["genres"][g] > 0 else 0 for g in all_genres]
        data.append([row["song"], row["artist"]] + genre_vector)

    cols = ["song", "artist"] + all_genres
    df = pd.DataFrame(data, columns=cols)
    return df

def genre_by_artist_df(xml_tree, accepted_genres=None):
    """Build genre-by-artist DataFrame aggregated from songs in XML.
    Columns: ['artist', genre1, genre2, ...] with 1 if artist has any song in genre."""

    df_song = genre_by_song_df(xml_tree, accepted_genres)
    
    # Drop columns for song and artist but keep genre columns
    genre_cols = df_song.columns.difference(["song", "artist"])

    # Group by artist, aggregate genres using max (if any song has the genre => 1)
    df_artist = df_song.groupby("artist")[genre_cols].max().reset_index()

    return df_artist

# ----- Preprocessing -----

# ----- Binarization and Encoding ------





# def stage_1_build_tracks(tracks_json):
#     # create xml object
#     root = ET.Element("songs")
#     # get list of artists, and the list of songs for said artist
#     for artist, tracks in tracks_json.items():
#         # for each track for said artist, create an object and add data
#         for track in tracks:
#             song_elem = ET.SubElement(root, "song", name=track["name"])
#             ET.SubElement(song_elem, "playcount").text = track["playcount"]
#             ET.SubElement(song_elem, "listeners").text = track["listeners"]
#             ET.SubElement(song_elem, "mbid").text = track.get("mbid", "")
#             ET.SubElement(song_elem, "url").text = track["url"]
#             ET.SubElement(song_elem, "artist").text = artist
    
#     # return xml object
#     return root

# def stage_2_add_tags(root, tags_json):
#     # Index songs for fast lookup by artist + song name
#     songs_index = {}
#     for song_elem in root.findall("song"):
#         # song name attr is unique only within artist, so we need artist text inside song elem to key map
#         key = (song_elem.find("artist").text, song_elem.attrib["name"])
#         songs_index[key] = song_elem
    
#     # get list of artists, and the list of songs for said artist
#     for artist, tracks_dict in tags_json.items():
#         # get each song and said song's list of tags
#         for song_name, tags in tracks_dict.items():
#             key = (artist, song_name)
#             if key in songs_index:
#                 song_elem = songs_index[key]  # get song element
#                 tags_elem = ET.SubElement(song_elem, "tags")  # crate tag element
#                 for tag in tags:
#                     tag_elem = ET.SubElement(tags_elem, "tag", count=str(tag["count"]))  # add specific tag to list with count
#                     tag_elem.text = tag["name"]  # set name of object

# def gather_tag_counts(root):
#     tag_counts = {}
#     for song_elem in root.findall("song"):
#         tags_elem = song_elem.find("tags")
#         if tags_elem is None:
#             continue
#         for tag_elem in tags_elem.findall("tag"):
#             name = tag_elem.text
#             count = int(tag_elem.attrib.get("count", "0"))
#             tag_counts[name] = tag_counts.get(name, 0) + count

#     print(str(tag_counts))
#     return tag_counts

# def get_sorted_tag_counts(tag_counts):
#     sorted_tag_counts = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
#     return sorted_tag_counts

# def get_top_tags(tag_counts, n=TOP_N_TAGS):
#     # sort by count descending and pick top n
#     sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
#     return [tag for tag, _ in sorted_tags[:n]]

# def build_artist_genre_matrix(root, top_tags, threshold=THRESHOLD):
#     artist_tag_sums = {}
#     for song_elem in root.findall("song"):
#         artist = song_elem.find("artist").text
#         if artist not in artist_tag_sums:
#             artist_tag_sums[artist] = {tag:0 for tag in top_tags}
#         tags_elem = song_elem.find("tags")
#         if tags_elem is None:
#             continue
#         for tag_elem in tags_elem.findall("tag"):
#             name = tag_elem.text
#             count = int(tag_elem.attrib.get("count", "0"))
#             if name in top_tags:
#                 artist_tag_sums[artist][name] += count

#     # binarize (> threshold)
#     for artist in artist_tag_sums:
#         for tag in top_tags:
#             artist_tag_sums[artist][tag] = 1 if artist_tag_sums[artist][tag] > threshold else 0

#     return artist_tag_sums

# def build_song_genre_matrix(root, top_tags, threshold=THRESHOLD):
#     song_tag_counts = {}
#     for song_elem in root.findall("song"):
#         song_name = song_elem.attrib["name"]
#         tag_sum = {tag:0 for tag in top_tags}
#         tags_elem = song_elem.find("tags")
#         if tags_elem is not None:
#             for tag_elem in tags_elem.findall("tag"):
#                 name = tag_elem.text
#                 count = int(tag_elem.attrib.get("count", "0"))
#                 if name in top_tags:
#                     tag_sum[name] += count
#         # binarize
#         song_tag_counts[song_name] = {
#             tag: 1 if count > threshold else 0 for tag, count in tag_sum.items()
#         }
#     return song_tag_counts

# def write_csv_pandas(filename, data_dict, top_tags, index_label):
#     # data_dict = {row_name: {tag: val}}
#     df = pd.DataFrame.from_dict(data_dict, orient='index')
#     # enforce column order
#     df = df[top_tags]
#     df.index.name = index_label
#     df.to_csv(filename)

# def main():
#     print("--> Removing old output file...")

#     # remove old output file
#     if os.path.exists(OUTPUT_XML):
#         os.remove(OUTPUT_XML)

#     print("--> Opening input data files...")

#     with open(ARTIST_TRACKS_FILE, "r") as f:
#         # load artists into python-friendly json
#         tracks_json = json.load(f)
#     with open(TRACK_TAGS_FILE, "r") as f:
#         # same here, for track tags
#         tags_json = json.load(f)

#     # build xml structure containing all songs, including necessary data
#     print("--> Reading artist top songs into xml structure...")
#     root = stage_1_build_tracks(tracks_json)
#     print("--> Reading track tags and adding tags to songs...")
#     stage_2_add_tags(root, tags_json)

#     print("--> Writing single-line xml...")
#     tree = ET.ElementTree(root)
#     tree.write(OUTPUT_SINGLE_XML, encoding="utf-8", xml_declaration=True)

#     print("--> Prettifying xml...")
#     with open(OUTPUT_SINGLE_XML, "r") as OriginalXML:
#         with open(OUTPUT_XML, "w") as output:
#             temp = xml.dom.minidom.parseString(OriginalXML.read())
#             New_XML = temp.toprettyxml()
#             output.write(New_XML)

#     print("--> Removing old single line xml...")
#     # remove old output (single line) file
#     if os.path.exists(OUTPUT_SINGLE_XML):
#         os.remove(OUTPUT_SINGLE_XML)

#     print("--> gather top tags & counts of tags...")
#     tag_counts = gather_tag_counts(root)
#     top_tags = get_top_tags(tag_counts)

#     with open("SORTED_TAGS.csv", "w") as sorted_tags_file:
#         for item in get_sorted_tag_counts(tag_counts):
#             sorted_tags_file.write(item[0] + "," + str(item[1]) + "\n")

#     print("  > Top " + str(TOP_N_TAGS) + " tags:")
#     for item in top_tags:
#         print("  - " + str(item))
    

#     print("--> Building artist csv...")
#     artist_matrix = build_artist_genre_matrix(root, top_tags)
#     write_csv_pandas(OUTPUT_GBA, artist_matrix, top_tags, "artist")

#     print("--> Building song csv...")
#     song_matrix = build_song_genre_matrix(root, top_tags)
#     write_csv_pandas(OUTPUT_GBS, song_matrix, top_tags, "song")

#     print("-- Done! --")


def extract_genres_from_tags(tags_elem):
    """Extract genre counts from a <tags> element as {genre: count}."""
    if tags_elem is None:
        return {}
    genres = {}
    for tag_elem in tags_elem.findall("tag"):
        genre = tag_elem.text.lower()  # normalize to lowercase
        count = int(tag_elem.attrib.get("count", "0"))
        genres[genre] = count
    return genres



def main():
    print("----- Starting Preprocessing... -----")

    # 1.  remove old output files if they exist
    print("--> Removing old output files...")
    remove_old_output_files()

    # 2.  read artist and tracks into json
    artist_tracks_json = read_json(FI_ARTISTS)
    track_tags_json = read_json(FI_TAGS)

    # 3.  combine data from artist's songs and their tags into one xml
    combined_xml: ET.ElementTree = build_combined_xml(artist_tracks_json, track_tags_json)

    # 3.5 [Optionally add encodings to song and artist here and add to xml]

    # Optionally define accepted genres list (lowercased)
    accepted_genres_lower = set(g.lower() for g in GENRES)

    # 4.  create a pandas df for genre by song
    df_genres_by_song = genre_by_song_df(combined_xml, accepted_genres_lower)

    # 5.  create a pandas dataframe for genre by artist
    df_genres_by_artist = genre_by_artist_df(combined_xml, accepted_genres_lower)






    # # 6. Encode song names and artist names
    # song_encoder = LabelEncoder()
    # df_genres_by_song['song_id'] = song_encoder.fit_transform(df_genres_by_song['song'])

    # artist_encoder = LabelEncoder()
    # df_genres_by_song['artist_id'] = artist_encoder.fit_transform(df_genres_by_song['artist'])

    # # 2. Create MultiLabelBinarizer for genres of songs
    # genre_cols = df_genres_by_song.columns.difference(['song', 'artist', 'song_id', 'artist_id'])

    # mlb = MultiLabelBinarizer()

    # # Extract multi-label genre lists for each song
    # genre_lists = []
    # for _, row in df_genres_by_song.iterrows():
    #     genres_for_song = [g for g in genre_cols if row[g] == 1]
    #     genre_lists.append(genres_for_song)

    # genre_matrix = mlb.fit_transform(genre_lists)

    # # genre_matrix is a numpy array: row=song, col=genre (1/0)
    # # mlb.classes_ gives the ordered genre list

    # # --- Save encoders ---
    # import pickle
    # with open("song_encoder.pkl", "wb") as f:
    #     pickle.dump(song_encoder, f)
    # with open("artist_encoder.pkl", "wb") as f:
    #     pickle.dump(artist_encoder, f)
    # with open("genre_mlb.pkl", "wb") as f:
    #     pickle.dump(mlb, f)









    # 4.  using a list of just artist names, create an Encoder and id them
    

    # 5.  using a list of just song names, create an Encoder and id them

    combined_xml.write(FO_COMB_XML, encoding="utf-8", xml_declaration=True)

    write_csv(df_genres_by_artist, FO_GBA, FO_GBA_PKL)
    write_csv(df_genres_by_song, FO_GBS, FO_GBS_PKL)







    
    # 6.  Insert song ID's into song elements as an attribute `songID`

    # 7.  Insert arist ID's into song elements as an attribute `artistID`

    # 6.  Insert artist id into attribute of songs
    #     (find matching artist name, insert their id: artistID)

    # 4.  write raw combined xml

    # 5.  clean xml
    #     - remove unnecessary attributes
    #       - really just need to keep name and list of genres
    #     - remove tags from (songs and artists) that aren't in list of accepted genres
    #     - remove (songs and artists) that don't match any accepted genres
    #     - convert count to 1 or 0 depending on whether it satisfies the threshold
    
    # 6.  write cleaned, combined xml
    
    # 7.  Create a pandas dataframe for genre by artist
    #     - header: name, [genre name ...]
    #     - line by line (I'm sure there's a better way) add a row with name, then all genre matches (1 or 0)

    # 8.  Create a pandas dataframe for genere by song (similar to artist)

    # 9.  Write Outputs:
    #     - genre-by-artist CSV
    #     - genre-by-song CSV

    # 10. Write .pkl's:
    #     - Artist IDs
    #     - Song IDs
    #     - genre-by-artist multilabel encoder
    #     - genre-by-song multilabel encoder

if __name__ == "__main__":
    main()
