# Every Pokemon Card

A bot that tweets random Pokemon cards.

Set up:

1. `pip install tweepy`.
2. Export environment variables.
3. `python3 {filename}` to run.

## Environment Variables

Environment variables can be fetched from AWS. They should be added to this repo
in a file called `.env.local`:

```bash
TWITTER_CONSUMER_KEY=...
TWITTER_CONSUMER_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

If the variables are not set, you may see an error like this:

```bash
tweepy.error.TweepError: Failed to send request: Only unicode objects are escapable. Got None of type <class 'NoneType'>.
```

## Publishing

### Dependencies

To bundle up dependencies, run:

```bash
pip install -t lambda_function -r requirements.txt
```

To bundle up the code, add the main.py file to the lambda directory. Zip this
directory and upload it to AWS Lambda.

## main.py

This script fetches a card from a Pokemon TCG API and tweets it.
