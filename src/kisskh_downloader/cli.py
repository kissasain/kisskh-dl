from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse
import click
import validators
from kisskh_downloader.downloader import Mu38Extracter, Mu3u8Selector

from kisskh_downloader.kisskh_api import KissKHApi
from kisskh_downloader.utils import get_matching_quality


@click.group()
def kisskh():
    pass


@kisskh.command()
@click.argument("drama_url_or_name")
@click.option(
    "--first",
    "-f",
    type=click.INT,
    default=1,
    help="Starting episode number."
)
@click.option(
    "--last",
    "-l",
    type=click.INT,
    default=sys.maxsize,
    help="Ending episode number."
)
@click.option(
    "--quality",
    "-q",
    default="1080p",
    type=click.Choice(["360p", "480p", "540p", "720p", "1080p"]),
    help="Quality of the video to be downloaded.",
)
@click.option(
    "--output-dir",
    "-o",
    default=Path.home() / "Downloads",
    help="Output directory where downloaded files will be store.",
)
def dl(
    drama_url_or_name: str, first: int, last: int, quality: str, output_dir
) -> None:
    kisskh_api = KissKHApi()
    if validators.url(drama_url_or_name):
        parsed_url = urlparse(drama_url_or_name)
        drama_id = parse_qs(parsed_url.query)["id"][0]
        drama_name = parsed_url.path.split("/")[-1].replace("-", "_")
    else:
        drama = kisskh_api.get_drama_by_query(drama_url_or_name)
        drama_id, drama_name = drama.id, drama.title

    episode_web_urls = kisskh_api.get_episode_urls(drama_id=drama_id, start=first, stop=last)

    m3u8_extracter = Mu38Extracter()
    for episode_number, episode_web_url in episode_web_urls.items():
        url = m3u8_extracter.extract(episode_web_url[1])[0]
        ms = Mu3u8Selector(url)
        videos = ms.get_segments_mapping()
        downloadable_quality = get_matching_quality(quality, videos.keys())
        outfile = (
            f"{output_dir}/{drama_name}/{drama_name}_{quality}_E{episode_number:02d}.ts"
        )
        ms.download_playlist_segments(outfile, videos.get(downloadable_quality))


if __name__ == "__main__":
    kisskh()
