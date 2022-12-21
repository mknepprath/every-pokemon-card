import os
import random

import requests
import tweepy
from mastodon import Mastodon


def lambda_handler(event, context):
    consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    mastodon = Mastodon(
        api_base_url='https://mastodon.social',
        client_id=os.environ.get('MASTODON_CLIENT_KEY'),
        client_secret=os.environ.get('MASTODON_CLIENT_SECRET'),
        access_token=os.environ.get('MASTODON_ACCESS_TOKEN'),
    )

    response = requests.get(
        'https://api.pokemontcg.io/v2/cards?page=1&pageSize=1')
    json = response.json()
    total_count = json['totalCount']

    # get a random number between 1 and total_count
    random_number = random.randint(1, total_count)

    # query pokemontcg API for a random card
    # example query: https://api.pokemontcg.io/v2/cards?page=12022&pageSize=1
    response = requests.get(
        'https://api.pokemontcg.io/v2/cards?page=%s&pageSize=1' % random_number)
    json = response.json()

    image = json["data"][0]["images"]["large"]
    name = json["data"][0]["name"]
    tcgSet = json["data"][0]["set"]["name"]
    releaseDate = json["data"][0]["set"]["releaseDate"]
    artist = json["data"][0]["artist"]

    filename = "/tmp/temp.png"
    request = requests.get(image, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        alt_text = "%s (%s) released %s. Illustrated by %s." % (
            name, tcgSet, releaseDate, artist)

        twitter_media_response = api.media_upload(filename=filename)
        api.create_media_metadata(
            twitter_media_response.media_id, alt_text=alt_text)
        if twitter_media_response.media_id:
            api.update_status(status=name, media_ids=[
                twitter_media_response.media_id])

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
