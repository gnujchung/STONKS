import twitter
import csv
import time
import sys
import re
from nltk.tokenize import word_tokenize
import string
from nltk.corpus import stopwords
import json
import nltk

'''
TODO:
    find more data (too neutral for now)
        - added happy.txt and sad.txt --- not enough
    clean up code
    search for all 30 in DOW
        -DONE
    refine search to pull from stock accts
'''

#test set should be at least len 100 when actually running model
    #set to 10 for testing to not reach 180 tweets/15 min API allows
TEST_SET_SIZE = 180
EXCEL_CREATED = True
KEYWORDS = [
    "AAPL", "AXP", "BA", "CAT", "CSCO", "CVX", "DIS", "DOW", "GS", "HD", "IBM",
    "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE", "PFE", "PG",
    "TRV", "UNH", "UTX", "V", "VZ", "WBA", "WMT", "XOM"
]

#open API keys (omit first line as it contains format)
twitterKeys = open("API.txt", 'r').read().splitlines()[1:]

twittApi = twitter.Api(consumer_key=twitterKeys[0],
                        consumer_secret=twitterKeys[1],
                        access_token_key=twitterKeys[2],
                        access_token_secret=twitterKeys[3])

############################### Build Test Set #################################

def buildTestSet(searchWord, testSetSize):
    print("Searching for:", testSetSize, "tweets with:", searchWord)
    try:
        tweets = twittApi.GetSearch(searchWord, count=testSetSize, lang="en")
        print("Found:", len(tweets), "tweets for:", searchWord)
        out = [{"text":status.text, "label":None} for status in tweets]

        #UnicodeEncodeError can occur (define error behavior as remmove non ascii)
        for i in range(len(out)):
            out[i]["text"] = ''.join(filter(lambda x: x in set(string.printable), out[i]["text"]))

        return out
    except Exception as e:
        print("Exception raised:", e)
        return None
testDataSet = []
for key in KEYWORDS:
    testDataSet.append(buildTestSet(key, TEST_SET_SIZE//len(KEYWORDS)))
if testDataSet == []:
    sys.exit("ABORT: testSet empty")

print("testDataSet complete")

############################## Build Training Set ##############################

def buildOrigTrainingSet(corpusFile, tweetDataFile):
    trainingDataSet = []

    #If excels already been created, we dont have to redo building, check global
    if EXCEL_CREATED:
        with open(tweetDataFile,'r') as csvfile:
            lineReader = csv.reader(csvfile,delimiter=',',quotechar="\"")
            for row in lineReader:
                if row != []:
                    objJson = {}
                    objJson["tweet_id"] = row[0]
                    objJson["text"] = row[1]
                    objJson["label"] = row[2]
                    objJson["topic"] = row[3]
                    trainingDataSet.append(objJson)
        return trainingDataSet

    corpus = []

    with open(corpusFile,'r') as csvfile:
        lineReader = csv.reader(csvfile,delimiter=',', quotechar="\"")
        for row in lineReader:
            corpus.append({"tweet_id":row[2], "label":row[1], "topic":row[0]})

    rate_limit = 180
    sleep_time = 900/rate_limit

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

def altTrainingSet(goodFile, badFile):
    def returnDict(line, sentiment):
        return {"tweet_id": "", "text": line.strip(), "label": sentiment, "topic": ""}
    resLst = []
    goodFile = open(goodFile, 'r')
    for line in goodFile:
        resLst.append(returnDict(line, 'positive'))
    for line in badFile:
        resLst.append(returnDict(line, 'negative'))
    return resLst

print("\n\n----------------BUILDING TRAINING SET----------------\n\n")
trainingData = buildOrigTrainingSet("corpus.csv", "tweetDataFile.csv")
trainingData += altTrainingSet("happy.txt", "sad.txt")
print("training data built")

################################################################################
class PreProcessTweets:
    def __init__(self):
        self._stopwords = set(stopwords.words("english") + list(string.punctuation) + ["AT_USER", "URL"])

    def _processTweet(self, tweet):
        tweet = tweet.lower() # convert text to lower-case
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet) # remove URLs
        tweet = re.sub('@[^\s]+', 'AT_USER', tweet) # remove usernames
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet) # remove the # in #hashtag
        tweet = word_tokenize(tweet) # remove repeated characters (helloooooooo into hello)
        return [word for word in tweet if word not in self._stopwords]

    def processTweets(self, list_of_tweets):
        processedTweets=[]
        for tweet in list_of_tweets:
            processedTweets.append((self._processTweet(tweet["text"]),tweet["label"]))
        return processedTweets

print("\n\n----------------PROCESSING TWEETS----------------\n\n")

tweetProcessor = PreProcessTweets()
preprocessedTrainingSet = tweetProcessor.processTweets(trainingData)
preprocessedTestSet = []
for keySet in testDataSet:
    preprocessedTestSet.append(tweetProcessor.processTweets(keySet))

print("processing complete")

################################################################################
def buildVocabulary(preprocessedTrainingData):
    all_words = []

    for (words, sentiment) in preprocessedTrainingData:
        all_words.extend(words)

    wordlist = nltk.FreqDist(all_words)
    word_features = wordlist.keys()

    return word_features

def extract_features(tweet):
    tweet_words = set(tweet)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in tweet_words)
    return features

print("\n\n----------------RUNNING MODEL----------------\n\n")

word_features = buildVocabulary(preprocessedTrainingSet)
trainingFeatures = nltk.classify.apply_features(extract_features, preprocessedTrainingSet)

NBayesClassifier = nltk.NaiveBayesClassifier.train(trainingFeatures)

for i in range(len(preprocessedTestSet)):
    eachStock = preprocessedTestSet[i]
    NBResultLabels = [NBayesClassifier.classify(extract_features(tweet[0])) for tweet in eachStock]
    posRes = NBResultLabels.count('positive')
    negRes = NBResultLabels.count('negative')
    print("For keyword:", KEYWORDS[i], "positive val:", posRes, "negative val:", negRes)

    # get the majority vote
    if posRes == negRes:
        print("\tOverall Neutral Sentiment.", posRes, "out of:", TEST_SET_SIZE//len(KEYWORDS))
    elif posRes > negRes:
        print("\tOverall Positive Sentiment")
        print("\t\tPositive Sentiment Percentage = " + str(100*posRes/len(NBResultLabels)) + "%")
    else:
        print("\tOverall Negative Sentiment")
        print("\t\tNegative Sentiment Percentage = " + str(100*negRes/len(NBResultLabels)) + "%")
