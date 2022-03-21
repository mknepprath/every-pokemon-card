import os
import random

import requests
import tweepy


def lambda_handler(event, context):
    consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

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

    filename = "temp.png"
    request = requests.get(image, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        media_response = api.media_upload(filename=filename)
        api.update_status(status=name, media_ids=[media_response.media_id])

        os.remove(filename)
    else:
        print("Unable to download image")
