import argparse
from pathlib import Path
from textwrap import wrap

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import palbums
import pandas as pd
from PIL import Image
import seaborn as sns
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yaml

import tools


GRAPH_DIR = Path('Graphs')
GRAPH_DIR.mkdir(exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('-config', help='yaml config file')
config_path = parser.parse_args().config

args = yaml.load(Path(config_path).read_text(), Loader=yaml.SafeLoader)

if 'rcParams' in args.keys():
    for k, v in args['rcParams'].items():
        plt.rcParams[k] = v

if 'style' in args.keys():
    plt.style.use(args['style'])


auth = spotipy.SpotifyOAuth(
    redirect_uri='http://localhost:8888/callback', username=args['username']
)

sp = spotipy.Spotify(auth_manager=auth)

album = tools.get_album(sp, args['album_id'])

all_data = pd.concat(
    tools.Track(t).loudness(sp) for t in album['tracks']['items']
)
all_data['Centred Time'] = (
    all_data['Time'] 
    - (all_data.groupby('TrackNo')['Time'].transform('max') / 2)
)

g = sns.FacetGrid(
    data=all_data, sharex=True, sharey=True, row='Name', aspect=8, height=.8
)
g.map_dataframe(tools.plot_waves)

g.set_titles('{row_name}', c='C1', weight='bold', pad=2) 

for ax in g.axes.flatten():
    ax.set_axis_off()
    ax_min, ax_max = ax.get_xlim()
    
    ax.margins(x=0.003)

plt.tight_layout()
    
plt.savefig('body.png')

width = g.fig.get_size_inches()[0]

fig, ax = plt.subplots()
fig.set_size_inches(width, 3)
img = plt.imread(album['images'][0]['url'], format='jpg')
ax.imshow(img)
ax.set_axis_off()

name = album['name']

if len(name) > 40:
    title = '\n'.join(wrap(name, 40))
    size = 20
else:
    title = name
    size = 30
    
aname = ax.annotate(
    text=title, xy=(0.5, 0.28), xycoords='figure fraction', 
    size=size, weight='bold', ha='center', va='top', c='C1'
)

artists = ','.join(a['name'] for a in album['artists'])
bbox = aname.get_window_extent(fig.canvas.get_renderer())

art_text = ax.annotate(
    text=artists, xy=[(bbox.x0+bbox.x1)/2, bbox.y0-10], 
    xycoords='figure pixels', ha='center', va='top', size=size-5, c='C1'
)

for text in (aname, art_text):
    text.set_path_effects(
        [pe.withSimplePatchShadow(shadow_rgbFace='C0', alpha=.3), pe.Normal()]
    )

plt.tight_layout()
fig.subplots_adjust(left=.3, right=.7, bottom=.3, top=.95)

plt.savefig('header.png')

header = Image.open('header.png')
body = Image.open('body.png')

both = Image.new('RGBA', size=(header.width, header.height+body.height))
both.paste(header, (0, 0))
both.paste(body, (0, header.height))
both.save(GRAPH_DIR / f'{name}.png')
