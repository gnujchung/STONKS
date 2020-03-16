import twitter
import csv
from time import sleep
from time import time
import sys
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import string

'''
TODO:
    add all data back in
    check all funcs
    refine search to pull from stock accts
    figure out stocks data set issues


    add elapsed time
        -DONE
    find more data (too neutral for now)
        - added happy.txt and sad.txt --- not enough
        - added stocksDataSet.csv --DONE
    prune all "irrelevant" data from original dataset
        -DONE
    search for all 30 in DOW
        -DONE
    remove extra dict keys
        -DONE
    clean up code
        -DONE
    cut words w less than 3 char out
        -DONE
    check data after processed
        - duplicates from original data set
            -DONE --- rt counting
        - ellipsis appearing
            -DONE
        - .AT_USER
            -DONE
        - remove all tickers from tweets (create set and check if word not in)
            -DONE
        - remove all numbers
            -DONE
'''

TEST_SET_SIZE = 3000 # total number of tweets fetched for the testing data
EXCEL_CREATED = True #tweetDataFile.csv was built by manually requesting the tweets
KEYWORDS = [
    "AAPL", "AXP", "BA", "CAT", "CSCO", "CVX", "DIS", "DOW", "GS", "HD", "IBM",
    "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE", "PFE", "PG",
    "TRV", "UNH", "UTX", "V", "VZ", "WBA", "WMT", "XOM"
]

origTime = currTime = time()

# open API keys (omit first line as it contains format)
# API keys should NOT be stored in github repo, request keys from Tony if needed
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
        sys.exit("ABORT: Twitter API error for: " + searchWord)

testDataSet = []
for key in KEYWORDS:
    testDataSet.append(buildTestSet(key, TEST_SET_SIZE//len(KEYWORDS)))
newTime = time()
elapsed = round(newTime - currTime, 2)
currTime = newTime
print("testDataSet complete in", elapsed, "seconds")

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
                    objJson["text"] = row[0]
                    objJson["label"] = row[1]
                    trainingDataSet.append(objJson)
        csvfile.close()
        return trainingDataSet

    corpus = []

    with open(corpusFile,'r') as csvfile:
        lineReader = csv.reader(csvfile,delimiter=',', quotechar="\"")
        for row in lineReader:
            corpus.append({"tweet_id":row[2], "label":row[1]})
    csvfile.close()

    rate_limit = 180
    sleep_time = 900/rate_limit

    for tweet in corpus:
        try:
            status = twittApi.GetStatus(tweet["tweet_id"])
            print("Tweet fetched:", status.text)
            tweet["text"] = status.text
            del tweet["tweet_id"]
            trainingDataSet.append(tweet)
            sleep(sleep_time)
        except Exception as e:
            print("Exception raised:", e)
            continue

    # now we write them to the empty CSV file
    with open(tweetDataFile,'w') as csvfile:
        linewriter = csv.writer(csvfile,delimiter=',',quotechar="\"")
        for tweet in trainingDataSet:
            try:
                linewriter.writerow([tweet["text"], tweet["label"]])
            except Exception as e:
                print(e)
    csvfile.close()
    return trainingDataSet

def dualTrainingSet(goodFile, badFile):
    resLst = []
    goodFile = open(goodFile, 'r')
    for line in goodFile:
        resLst.append({"text": line.strip(), "label": "positive"})
    badFile = open(badFile, 'r')
    for line in badFile:
        resLst.append({"text": line.strip(), "label": "negative"})
    goodFile.close(); badFile.close()
    return resLst

def stocksTrainingSet(fileName):
    resLst = []
    with open(fileName,'r') as csvfile:
        lineReader = csv.reader(csvfile,delimiter=',',quotechar="\"")
        for row in lineReader:
            resLst.append({"text": row[1], "label": row[2]})
    csvfile.close()
    return resLst


print("\n\n----------------BUILDING TRAINING SET----------------\n\n")
trainingData = buildOrigTrainingSet("corpus.csv", "tweetDataFile.csv")
trainingData += dualTrainingSet("happy.txt", "sad.txt")
trainingData += stocksTrainingSet("stocksDataSet.csv")
newTime = time()
elapsed = round(newTime - currTime, 2)
currTime = newTime
print("training data built in:", elapsed, "seconds")

################################################################################

class PreProcessTweets:
    def __init__(self):
        self._stopwords = set(stopwords.words("english") + list(string.punctuation) \
            + ["AT_USER", "URL", ".AT_USER", "..."] + [tick.lower() for tick in KEYWORDS])

    def _processTweet(self, tweet):
        def isFloat(word):
            try: float(word); return True
            except: return False
        def isValid(word):
            return word not in self._stopwords and len(word) > 2 and not isFloat(word)
        tweet = tweet.lower() # convert text to lower-case
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet) # remove URLs
        tweet = re.sub('@[^\s]+', 'AT_USER', tweet) # remove usernames
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet) # remove the # in #hashtag
        tweet = word_tokenize(tweet) # remove repeated characters (helloooooooo into hello)
        return [word for word in tweet if isValid(word)]

    def processTweets(self, list_of_tweets):
        processedTweets = []
        for tweet in list_of_tweets:
            processedTweets.append((self._processTweet(tweet["text"]),tweet["label"]))
        return processedTweets

print("\n\n----------------PROCESSING TWEETS----------------\n\n")

tweetProcessor = PreProcessTweets()
preprocessedTrainingSet = tweetProcessor.processTweets(trainingData)
preprocessedTestSet = []
for keySet in testDataSet:
    preprocessedTestSet.append(tweetProcessor.processTweets(keySet))

newTime = time()
elapsed = round(newTime - currTime, 2)
currTime = newTime
print("processing complete in:", elapsed, "seconds")

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

print("\n\n----------------TRAINING MODEL----------------\n\n")

word_features = buildVocabulary(preprocessedTrainingSet)
trainingFeatures = nltk.classify.apply_features(extract_features, preprocessedTrainingSet)

print("training")
NBayesClassifier = nltk.NaiveBayesClassifier.train(trainingFeatures)
newTime = time()
elapsed = round(newTime - currTime, 2)
currTime = newTime
print("training complete in:", elapsed, "seconds")

################################################################################

print("\n\n----------------RUNNING MODEL----------------\n\n")

for i in range(len(preprocessedTestSet)):
    eachStock = preprocessedTestSet[i]
    NBResultLabels = [NBayesClassifier.classify(extract_features(tweet[0])) for tweet in eachStock]
    posRes = NBResultLabels.count('positive')
    negRes = NBResultLabels.count('negative')
    print("For keyword:", KEYWORDS[i], "positive val:", posRes, "negative val:", negRes)

    # get the majority vote
    if posRes == negRes:
        print("\tOverall Neutral Sentiment.", posRes+negRes, "out of:", len(eachStock))
    elif posRes > negRes:
        print("\tOverall Positive Sentiment")
        print("\t\tPositive Sentiment Percentage = " + str(100*posRes/len(NBResultLabels)) + "%")
    else:
        print("\tOverall Negative Sentiment")
        print("\t\tNegative Sentiment Percentage = " + str(100*negRes/len(NBResultLabels)) + "%")
    newTime = time()
    elapsed = round(newTime - currTime, 2)
    currTime = newTime
    print(KEYWORDS[i], "completed in:", elapsed, "seconds")

print("running complete in:", round(time() - origTime, 2), "seconds")
