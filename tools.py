import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DATA_DIR = Path('Data')
DATA_DIR.mkdir(exist_ok=True)


def get_album(client, album_id):
    album_dir = DATA_DIR / 'albums'
    album_dir.mkdir(exist_ok=True, parents=True)
    
    file_path = album_dir / f'{album_id}.json'
    
    if file_path.is_file():
        print('Reading saved data')
        content = json.loads(file_path.read_text(encoding='utf8'))
    else:
        print('New connection')
        content = client.album(album_id)
        file_path.write_text(json.dumps(content, indent=4), encoding='utf8')
        
    return content


def get_audio_features(client, track_ids, name):
    feat_dir = DATA_DIR / 'audio features'
    feat_dir.mkdir(exist_ok=True, parents=True)
    
    file_path = feat_dir / f'{name}.json'
    
    if file_path.is_file():
        print('Reading saved data')
        content = json.loads(file_path.read_text(encoding='utf8'))
    else:
        print('New connection')
        content = client.audio_features(track_ids)
        file_path.write_text(json.dumps(content, indent=4), encoding='utf8')
        
    return content


def get_audio_analysis(client, song_id):
    album_dir = DATA_DIR / 'songs'
    album_dir.mkdir(exist_ok=True, parents=True)
    
    file_path = album_dir / f'{song_id}.json'
    
    if file_path.is_file():
        print('Reading saved data')
        content = json.loads(file_path.read_text(encoding='utf8'))
    else:
        print('New connection')
        content = client.audio_analysis(song_id)
        file_path.write_text(json.dumps(content, indent=4), encoding='utf8')
        
    return content


class Track:
    def __init__(self, data_dict):
        self._data = data_dict
        self.name = self._data['name']
        self.id = self._data['id']
        self.track_number = self._data['track_number']
    
    def loudness(self, client, first_resample='500ms', second_resample='50ms'):
        res = get_audio_analysis(client, self.id)
        
        times = []

        for seg in res['segments']:
            times.append({
                'Time': seg['start'], 
                'Loudness': seg['loudness_start']
            })
            times.append({
                'Time': seg['start'] + seg['loudness_max_time'], 
                'Loudness': seg['loudness_max']
            })
            if seg['loudness_end'] != 0:
                times.append({
                    'Time': seg['start'] + seg['duration'], 
                    'Loudness': seg['loudness_end']
                })
            
        raw = pd.DataFrame(times) 
        raw['Time'] = pd.to_datetime(raw['Time'], unit='s')

        df = raw.copy(deep=True)
        df = df.set_index('Time').resample(first_resample, closed='left')\
               .min()\
               .resample(second_resample).interpolate(method='quadratic')\
               .reset_index()

        df['Time'] = (df['Time'] - df['Time'].dt.normalize()).dt.total_seconds()

        df['Loudness'] = df['Loudness'].min() - df['Loudness']

        df['Loudness_invert'] = -df['Loudness']
        
        return df.assign(Name=self.name, TrackNo=self.track_number)


def plot_waves(data, color, x='Centred Time',
               y1='Loudness', y2='Loudness_invert', 
               line_dict=None, fill_dict=None, *args, **kwargs):
    line_local = {'lw': 2, 'solid_capstyle': 'round'}
    if line_dict:
        for k, v in line_dict.items():
            line_local[k] = v

    fill_local = {'alpha': .6}
    if fill_dict:
        for k, v in fill_dict.items():
            fill_local[k] = v
    
    ax = plt.gca()
    data.plot.line(
        x=x, y=y1, c=color, legend=False, ax=ax, **line_local
    )
    data.plot.line(
        x=x, y=y2, c=color, legend=False, ax=ax, **line_local
    )

    ax.fill_between(x=data[x], y1=data[y1], y2=data[y2], fc=color, **fill_local)
    
    for _, row in data.iloc[[0, -1]].iterrows():
        ax.plot([row[x], row[x]], [row[y1], row[y2]], c=color, **line_local)
