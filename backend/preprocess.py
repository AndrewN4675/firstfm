### NOTE: Most of this code is based on JohnnyBoiTime's Movie NN code! Props to him

import pandas as pd
import os
import pickle
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom

# file location/name consts
ARTIST_TRACKS_FILE = "../artist_top_tracks.json"
TRACK_TAGS_FILE = "../track_tags.json"
OUTPUT_SINGLE_XML = "processed_single.xml"
OUTPUT_XML = "processed.xml"
OUTPUT_GBA = "genres_by_artist.csv"
OUTPUT_GBS = "genres_by_song.csv"

# number constants
THRESHOLD = 50
TOP_N_TAGS = 30

def stage_1_build_tracks(tracks_json):
    # create xml object
    root = ET.Element("songs")
    # get list of artists, and the list of songs for said artist
    for artist, tracks in tracks_json.items():
        # for each track for said artist, create an object and add data
        for track in tracks:
            song_elem = ET.SubElement(root, "song", name=track["name"])
            ET.SubElement(song_elem, "playcount").text = track["playcount"]
            ET.SubElement(song_elem, "listeners").text = track["listeners"]
            ET.SubElement(song_elem, "mbid").text = track.get("mbid", "")
            ET.SubElement(song_elem, "url").text = track["url"]
            ET.SubElement(song_elem, "artist").text = artist
    
    # return xml object
    return root

def stage_2_add_tags(root, tags_json):
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

def gather_tag_counts(root):
    tag_counts = {}
    for song_elem in root.findall("song"):
        tags_elem = song_elem.find("tags")
        if tags_elem is None:
            continue
        for tag_elem in tags_elem.findall("tag"):
            name = tag_elem.text
            count = int(tag_elem.attrib.get("count", "0"))
            tag_counts[name] = tag_counts.get(name, 0) + count
    return tag_counts

def get_top_tags(tag_counts, n=TOP_N_TAGS):
    # sort by count descending and pick top n
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags[:n]]

def build_artist_genre_matrix(root, top_tags, threshold=THRESHOLD):
    artist_tag_sums = {}
    for song_elem in root.findall("song"):
        artist = song_elem.find("artist").text
        if artist not in artist_tag_sums:
            artist_tag_sums[artist] = {tag:0 for tag in top_tags}
        tags_elem = song_elem.find("tags")
        if tags_elem is None:
            continue
        for tag_elem in tags_elem.findall("tag"):
            name = tag_elem.text
            count = int(tag_elem.attrib.get("count", "0"))
            if name in top_tags:
                artist_tag_sums[artist][name] += count

    # binarize (> threshold)
    for artist in artist_tag_sums:
        for tag in top_tags:
            artist_tag_sums[artist][tag] = 1 if artist_tag_sums[artist][tag] > threshold else 0

    return artist_tag_sums

def build_song_genre_matrix(root, top_tags, threshold=THRESHOLD):
    song_tag_counts = {}
    for song_elem in root.findall("song"):
        song_name = song_elem.attrib["name"]
        tag_sum = {tag:0 for tag in top_tags}
        tags_elem = song_elem.find("tags")
        if tags_elem is not None:
            for tag_elem in tags_elem.findall("tag"):
                name = tag_elem.text
                count = int(tag_elem.attrib.get("count", "0"))
                if name in top_tags:
                    tag_sum[name] += count
        # binarize
        song_tag_counts[song_name] = {
            tag: 1 if count > threshold else 0 for tag, count in tag_sum.items()
        }
    return song_tag_counts

def write_csv_pandas(filename, data_dict, top_tags, index_label):
    # data_dict = {row_name: {tag: val}}
    df = pd.DataFrame.from_dict(data_dict, orient='index')
    # enforce column order
    df = df[top_tags]
    df.index.name = index_label
    df.to_csv(filename)

def main():
    print("--> Removing old output file...")

    # remove old output file
    if os.path.exists(OUTPUT_XML):
        os.remove(OUTPUT_XML)

    print("--> Opening input data files...")

    with open(ARTIST_TRACKS_FILE, "r") as f:
        # load artists into python-friendly json
        tracks_json = json.load(f)
    with open(TRACK_TAGS_FILE, "r") as f:
        # same here, for track tags
        tags_json = json.load(f)

    # build xml structure containing all songs, including necessary data
    print("--> Reading artist top songs into xml structure...")
    root = stage_1_build_tracks(tracks_json)
    print("--> Reading track tags and adding tags to songs...")
    stage_2_add_tags(root, tags_json)

    print("--> Writing single-line xml...")
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_SINGLE_XML, encoding="utf-8", xml_declaration=True)

    print("--> Prettifying xml...")
    with open(OUTPUT_SINGLE_XML, "r") as OriginalXML:
        with open(OUTPUT_XML, "w") as output:
            temp = xml.dom.minidom.parseString(OriginalXML.read())
            New_XML = temp.toprettyxml()
            output.write(New_XML)

    print("--> Removing old single line xml...")
    # remove old output (single line) file
    if os.path.exists(OUTPUT_SINGLE_XML):
        os.remove(OUTPUT_SINGLE_XML)

    print("--> gather top tags & counts of tags...")
    tag_counts = gather_tag_counts(root)
    top_tags = get_top_tags(tag_counts)

    print("--> Building artist csv...")
    artist_matrix = build_artist_genre_matrix(root, top_tags)
    write_csv_pandas(OUTPUT_GBA, artist_matrix, top_tags, "artist")

    print("--> Building song csv...")
    song_matrix = build_song_genre_matrix(root, top_tags)
    write_csv_pandas(OUTPUT_GBS, song_matrix, top_tags, "song")

    print("-- Done! --")

if __name__ == "__main__":
    main()