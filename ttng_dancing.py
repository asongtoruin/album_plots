import json
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import palbums

from tools import get_album, get_audio_features


# Set up colour etc
plt.style.use('punisher')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Geomanist'
plt.rcParams['font.weight'] = 'regular'

colours = {
    'This Town Needs Guns': '#225e4f', 
    'Animals': '#d5b785', 
    '13.0.0.0.0':'#a8a9a6',
    'Disappointment Island': '#e2e993'
}


# API connection
auth = spotipy.SpotifyOAuth(
    redirect_uri='http://localhost:8888/callback', username='valeadam'
)

sp = spotipy.Spotify(auth_manager=auth)

# Set up folders
DATA_DIR = Path('Data')
OUTPUT_DIR = Path('TTNG Graphs')
OUTPUT_DIR.mkdir(exist_ok=True)

# Get all the album and track data
frames = []

for album in ('2217d2VN6Nn3zzU9mlApdK', '7n8f4VpR5BAC9IiLiiIWKl', '3QQOkN9iqJJrwXohbNYRiP', '6utXOCDpTDavsVbjQgPxpe'):
    alb_obj = get_album(sp, album)
    album_name = alb_obj['name']
    tracks = alb_obj['tracks']['items']
    audio_features = get_audio_features(
        sp, [t['id'] for t in tracks], name=album_name
    )

    # Combine tracks and features
    merged = pd.DataFrame(tracks)\
               .merge(pd.DataFrame(audio_features), on='id')\
               .assign(album=album_name)
    
    frames.append(merged)


df = pd.concat(frames, ignore_index=True)

# Split long track names
df['split_name'] = df['name'].apply(lambda txt: '\n'.join(wrap(txt, 30)))


# First, plot first album danceability
fig, ax = plt.subplots(figsize=(7,4))

first_album = df[df['album'].eq('This Town Needs Guns')]

first_album.plot.bar(
    x='split_name', y='danceability', fc=colours['This Town Needs Guns'], 
    legend=False,ax=ax, zorder=2
)

ax.set(
    yticks=[0, 0.5, 1], 
    yticklabels=['Lowest\nDanceability', 'Medium\nDanceability', 'Highest\nDanceability'],
    xlabel=None,
    ylabel=None,
)

ax.tick_params(length=0)
ax.spines['left'].set_visible(False)
ax.grid(zorder=1, alpha=.1, ls='--', axis='y')

plt.savefig(OUTPUT_DIR / 'ttng-album-danceability.png.png', bbox_inches='tight')


# Then, plot all albums danceability vs energy
fig, ax = plt.subplots(figsize=(6, 6))

sns.scatterplot(
    data=df, x='energy', y='danceability', hue='album', zorder=2, s=80, 
    palette=colours, linewidth=0, alpha=.8
)

ax.set(
    xticks=[0, 0.5, 1], 
    xticklabels=['Lowest\nEnergy', 'Medium\nEnergy', 'Highest\nEnergy'],
    yticks=[0, 0.5, 1], 
    yticklabels=['Lowest\nDanceability', 'Medium\nDanceability', 'Highest\nDanceability'],
    xlabel=None,
    ylabel=None,
)

ax.tick_params(length=0)

ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)

for side in ax.spines.keys():
    ax.spines[side].set_visible(False)

# Label maxima and minima, plus the song we're after
label_rows = [
    i for col in ('energy', 'danceability') 
    for i in [df[col].idxmax(), df[col].idxmin()]
]
label_rows.extend(df[df['name'].str.lower().str.startswith('26 is ')].index)

for _, row in df.iloc[label_rows].iterrows():
    energy, danceability = row[['energy', 'danceability']]
    if energy > 0.5:
        h_offset = 0.02
        ha='left'
    else:
        h_offset= -0.02
        ha='right'
    if row['name'].lower().startswith('26 is '):
        weight = 'bold'
    else:
        weight = 'regular'
    ax.annotate(
        xy=(energy, danceability), 
        xytext=(energy+h_offset, danceability),
        textcoords='data',
        text=row['name'], va='center', ha=ha,
        c=colours[row['album']], weight=weight
    )
    
ax.grid(zorder=1, alpha=.1, ls='--')
ax.legend(ncol=2, title=None, loc='upper center', bbox_to_anchor=(0.5, -0.1))
    
ax.set_aspect('equal', 'box')
plt.savefig(OUTPUT_DIR / 'ttng-dance-energy.png', bbox_inches='tight')
