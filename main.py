import os
import random
import time

import requests
# import tweepy
from mastodon import Mastodon


def get_json(url, attempts=5, timeout=6):
    """GET a URL and parse JSON, retrying the upstream's frequent 5xx.

    api.pokemontcg.io fails roughly half of all requests with a 500 or 502 whose
    body is either empty or the literal string "error code: 502". Neither parses,
    so calling .json() on the response raised JSONDecodeError and killed the run.
    That is why this posted 169 times against 720 scheduled runs.

    Status is checked before parsing, and both the request and the parse are
    retried with exponential backoff plus jitter -- jitter because this runs on a
    fixed cron, and a fixed backoff would retry in lockstep with every other
    client doing the same thing on the hour.
    """
    last = None
    for i in range(attempts):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            last = "HTTP %s" % response.status_code
        except (requests.RequestException, ValueError) as err:
            last = type(err).__name__
        if i < attempts - 1:
            time.sleep(min(2 ** i, 3) * (0.5 + random.random()))
    raise RuntimeError(
        "pokemontcg API failed after %d attempts (last: %s)" % (attempts, last))


def lambda_handler(event, context):
    # consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
    # consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    # auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
    # access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    # auth.set_access_token(access_token, access_token_secret)
    # api = tweepy.API(auth, wait_on_rate_limit=True)

    mastodon = Mastodon(
        api_base_url='https://mastodon.social',
        client_id=os.environ.get('MASTODON_CLIENT_KEY'),
        client_secret=os.environ.get('MASTODON_CLIENT_SECRET'),
        access_token=os.environ.get('MASTODON_ACCESS_TOKEN'),
    )

    json = get_json('https://api.pokemontcg.io/v2/cards?page=1&pageSize=1')
    total_count = json['totalCount']

    # get a random number between 1 and total_count
    random_number = random.randint(1, total_count)

    # query pokemontcg API for a random card
    # example query: https://api.pokemontcg.io/v2/cards?page=12022&pageSize=1
    json = get_json(
        'https://api.pokemontcg.io/v2/cards?page=%s&pageSize=1' % random_number)

    image = json["data"][0]["images"]["large"]
    name = json["data"][0]["name"]
    tcgSet = json["data"][0]["set"]["name"]
    releaseDate = json["data"][0]["set"]["releaseDate"]
    # Some cards have no artist field (seen 2026-10-04: KeyError: 'artist'),
    # so the alt text omits the credit rather than crashing the run.
    artist = json["data"][0].get("artist")

    filename = "/tmp/temp.png"
    request = None
    for i in range(3):
        request = requests.get(image, stream=True, timeout=10)
        if request.status_code == 200:
            break
        time.sleep(1 + random.random())
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        alt_text = "%s (%s) released %s." % (name, tcgSet, releaseDate)
        if artist:
            alt_text += " Illustrated by %s." % artist

        # twitter_media_response = api.media_upload(filename=filename)
        # api.create_media_metadata(
        #     twitter_media_response.media_id, alt_text=alt_text)
        # if twitter_media_response.media_id:
        #     api.update_status(status=name, media_ids=[
        #         twitter_media_response.media_id])

        mastodon_media_response = mastodon.media_post(
            filename, description=alt_text)
        if mastodon_media_response.id:
            mastodon.status_post(status=name, media_ids=[
                mastodon_media_response.id])

        os.remove(filename)
    else:
        print("Unable to download image")


# Uncomment to run locally:
# lambda_handler(None, None)
