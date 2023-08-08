from yandex_music import Client


def get_data(token: str) -> dict | Exception:
    try:
        client = Client(token).init()
        queues = client.queues_list()
        last_queue = client.queue(queues[0].id)
    except Exception as er:
        return er
    last_track_id = last_queue.get_current_track()
    last_track = last_track_id.fetch_track()
    artists = ', '.join(last_track.artists_name())
    link = f'https://music.yandex.ru/album/{last_track_id.album_id}/track/{last_track_id.track_id}'
    title = last_track.title
    cover = last_track.get_cover_url()
    data = {'state': artists, 'details': title, 'large_image': cover, 'small_image': 'logo'}
    data = {**data, 'buttons': [{"label": "Open in Yandex.Music", "url": link}]}
    return data
