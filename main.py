from os import getenv
from time import sleep
from dotenv import load_dotenv
from pypresence import Presence
from yandex_music import Client

load_dotenv()

CLIENT_ID: str = '980573087168876594'
TOKEN: str = getenv('TOKEN')

data: dict | None = {}

RPC = Presence(CLIENT_ID, pipe=0)
RPC.connect()

client = Client(TOKEN).init()
queues = client.queues_list()

while True:
    last_queue = client.queue(queues[0].id)
    last_track_id = last_queue.get_current_track()
    last_track = last_track_id.fetch_track()
    artists = ', '.join(last_track.artists_name())
    link = f'https://music.yandex.ru/album/{last_track_id.album_id}/track/{last_track_id.track_id}'
    title = last_track.title
    cover = last_track.get_cover_url()
    data = {'state': artists, 'details': title, 'large_image': cover, 'small_image': 'logo',
            'buttons': [{"label": "Открыть в Яндекс.Музыке", "url": link}]}
    RPC.update(**data)
    sleep(10)
