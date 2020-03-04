import twitter
import csv
import time
import sys

#test set should be len 100 when actually running model
    #set to 10 for testing to not reach 180 tweets/15 min API allows
TEST_SET_SIZE = 10

#open API keys (omit first line as it contains format)
twitterKeys = open("API.txt", 'r').read().splitlines()[1:]

twittApi = twitter.Api(consumer_key=twitterKeys[0],
                        consumer_secret=twitterKeys[1],
                        access_token_key=twitterKeys[2],
                        access_token_secret=twitterKeys[3])

############################### Build Test Set #################################

def buildTestSet(searchWord, testSetSize):
    print("Beginning Search with:", searchWord, "size:", testSetSize)
    try:
        tweets = twittApi.GetSearch(searchWord, count=testSetSize)
        print("Found:", len(tweets), "tweets for:", searchWord)
        out = [{"text":status.text, "label":None} for status in tweets]

        #UnicodeEncodeError can occur (define error behavior as replace with ?)
        sysEncoding = sys.stdout.encoding
        for i in range(len(out)):
            out[i]["text"] = out[i]["text"].encode(sysEncoding, errors="replace")
        return out
    except Exception as e:
        print("Exception raised:", e)
        return None

testDataSet = buildTestSet(input("Enter a search keyword:"), TEST_SET_SIZE)
if testDataSet == None:
    sys.exit("ABORT: error raised in testSet")

print("testDataSet:", testDataSet)

############################## Build Training Set ##############################

def buildTrainingSet(corpusFile, tweetDataFile):
    corpus = []

    with open(corpusFile,'r') as csvfile:
        lineReader = csv.reader(csvfile,delimiter=',', quotechar="\"")
        for row in lineReader:
            corpus.append({"tweet_id":row[2], "label":row[1], "topic":row[0]})

    rate_limit = 180
    sleep_time = 900/180

    trainingDataSet = []

    for tweet in corpus:
        try:
            status = twittApi.GetStatus(tweet["tweet_id"])
            print("Tweet fetched:", status.text)
            tweet["text"] = status.text
            trainingDataSet.append(tweet)
            time.sleep(sleep_time)
        except Exception as e:
            print("Exception raised:", e)
            continue

    # now we write them to the empty CSV file
    with open(tweetDataFile,'w') as csvfile:
        linewriter = csv.writer(csvfile,delimiter=',',quotechar="\"")
        for tweet in trainingDataSet:
            try:
                linewriter.writerow([tweet["tweet_id"], tweet["text"],
                    tweet["label"], tweet["topic"]])
            except Exception as e:
                print(e)
    return trainingDataSet

print("\n\n================BUILDING TRAINING SET================\n\n")
trainingData = buildTrainingSet("corpus.csv", "tweetDataFile.csv")
print("training data built")

################################################################################
