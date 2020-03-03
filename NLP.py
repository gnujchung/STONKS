import twitter

def buildTestSet(search_keyword):
    try:
        tweets_fetched = twittApi.GetSearch(search_keyword, count = 100)

        print("Fetched " + str(len(tweets_fetched)) + " tweets for the term " + search_keyword)

        return [{"text":status.text, "label":None} for status in tweets_fetched]
    except:
        print("Unfortunately, something went wrong..")
        return None

twitterKeys = open("API.txt", 'r').read().splitlines()[1:]

twittApi = twitter.Api(consumer_key=twitterKeys[0],
                        consumer_secret=twitterKeys[1],
                        access_token_key=twitterKeys[2],
                        access_token_secret=twitterKeys[3])

search_term = input("Enter a search keyword:")
testDataSet = buildTestSet(search_term)

print(testDataSet[0:4])
