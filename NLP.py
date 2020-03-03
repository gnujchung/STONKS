import twitter

twitterKeys = open("API.txt", 'r').read().splitlines()[1:]

twittApi = twitter.Api(consumer_key=twitterKeys[0],
                        consumer_secret=twitterKeys[1],
                        access_token_key=twitterKeys[2],
                        access_token_secret=twitterKeys[3])

print(twittApi.VerifyCredentials())
