#Will get all the nominees for a given award
# will need a different classifyer for movie awards than people awards
# from the set of tweets build a stopword list based on the awards and ceremony
# write some more regular expressions to improve our nomination tweet set

import json
from gg_api import buildConfidence
from gg_api import get_winner
from load_imdb import load_in
import nltk
import re
import en_core_web_sm
import string

#nlp = en_core_web_sm.load()

stop_words = nltk.corpus.stopwords.words('english')
stop_words += ["RT" + "congrats" + "woah" + "wow"]
award_stop_words = ["original", "song", "globe", "directora", "oscars", "oscar", "best", "picture", "motion", "drama", "golden", "globes", "goldenglobes", "actor", "actress", "musical", "comedy", "supporting", "director", "screenplay", "animated", "film", "films", "feature", "movie"]

#Initial Python File
def loadjson(file):
    #Load in JSON
    #JSON Structure:
    # { "text": whatever the text of the tweet holds
    #   "user": {screen name, user id}
    #   "id": tweet id
    #   "timestamp_ms": time of tweet (Long float structure)
    # }
    with open(file, "r") as fp:
        data = json.load(fp)
    return data

OFFICIAL_AWARDS = ['cecil b. demille award', 'best motion picture - drama', 'best performance by an actress in a motion picture - drama', 'best performance by an actor in a motion picture - drama', 'best motion picture - comedy or musical', 'best performance by an actress in a motion picture - comedy or musical', 'best performance by an actor in a motion picture - comedy or musical', 'best animated feature film', 'best foreign language film', 'best performance by an actress in a supporting role in a motion picture', 'best performance by an actor in a supporting role in a motion picture', 'best director - motion picture', 'best screenplay - motion picture', 'best original score - motion picture', 'best original song - motion picture', 'best television series - drama', 'best performance by an actress in a television series - drama', 'best performance by an actor in a television series - drama', 'best television series - comedy or musical', 'best performance by an actress in a television series - comedy or musical', 'best performance by an actor in a television series - comedy or musical', 'best mini-series or motion picture made for television', 'best performance by an actress in a mini-series or motion picture made for television', 'best performance by an actor in a mini-series or motion picture made for television', 'best performance by an actress in a supporting role in a series, mini-series or motion picture made for television', 'best performance by an actor in a supporting role in a series, mini-series or motion picture made for television']


# lets make a function that takes in a set of tweets and applies a regular expression
# simple helper function
# input: tweets -> set of all tweets, regex -> regular expression
# output: bool -> true if regex was matched, false otherwise
def tweetFilter(tweet, regex):
    #tweet_text = tweet['text']
    match = re.search(regex, tweet.lower())
    if match != None:
        return True
    else:
        return False

# helper function to get only nominated tweets for specific award
# input: tweets -> set of all tweets
# output: nom_tweets -> set of tweets with a form of nominate within
def get_nom_tweets(tweets, award_list):
    regex_list = [
        r"nomin((?:(?:at(?:ed|ion)))|ee)",
        r"(\bwant\b|wants|wanted|wanting|deserves?|deserved|should).*(win|won)",
        r".*(beat|beats).*",
        r".*(rooting).*",
        r".*(stole).*",
        r".*(misses|missed|miss).*"
    ]

    regex_blacklist = r"(presents|presenting|presentor|present|next year)"

    nom_tweets = []
    for tweet in tweets:
        for reg_exp in regex_list:
            regex = re.compile(reg_exp)
            if tweetFilter(tweet, regex) and not tweetFilter(tweet, regex_blacklist):
                #this means we matched our regex
                for award in award_list:
                    if award.lower() in tweet.lower():
                        nom_tweets.append(tweet)
                break
    return nom_tweets
    

# helper function to pull out all the named entities in a tweet
# input: tweet -> single tweet string
# output: name_list -> list of PERSON tagged chunks
def checkNames(tweet):
    # make sure that the PERSON is also a proper noun

    name_list = []

    #tokenize tweet
    tokens = nltk.word_tokenize(tweet)
    tagged = nltk.pos_tag(tokens)
    entities = nltk.ne_chunk(tagged)
    # loop through chunks to find the person    
    for chunk in entities:

        #only look at the trees
        if type(chunk) == nltk.tree.Tree:
            if chunk.label() == 'PERSON':
                name_string = ""
                for leaf in chunk.leaves():
                    if leaf[0].lower() not in award_stop_words and leaf[1] == "NNP":

                        name_string += leaf[0] + " "
                if name_string != "":
                    name_list.append(name_string)

    return name_list

# function to create tweet dictionary (lets just get some names)
def buildNameList(tweet_set):
    full_name_list = []
    for tweet in tweet_set:

        # check if the name list is empty
        full_name_list += checkNames(tweet)

    return full_name_list

def countNamesActor(name_list):
    full_count_dict = {}

    # checks each name against our list of names
    
    for name in name_list:
        full_count_dict[name] = full_count_dict.get(name, 0) + 1

    new_dict = {}
    for key, val in full_count_dict.items():

        if len(key.split()) >= 2:
            new_dict[key] = val

    for key, val in new_dict.items():
        for key2, val2 in full_count_dict.items():
            if key in key2:
                new_dict[key] += val2
    
    return new_dict

def countNamesMovie(name_list):
    full_count_dict = {}
    
    for name in name_list:
        full_count_dict[name] = full_count_dict.get(name, 0) + 1
    return full_count_dict

def actorCheck(actor_list, name_dict):
    new_list = []
    for name in name_dict:

        name_text = name[0].replace(" ", "")
        for actor in actor_list:

            actor_text = actor.replace(" ", "")
            if name_text in actor_text and len(actor.split()) >= 2:
                new_list.append(name)
                break

    return new_list

#award example: best performance actress motion picture drama
#desired outomce: ["best director motion picture", "best director motion", "best director"]
# award is inputed as a string
def getFinalNoms(award, year):
    cleaned_tweet_data = loadjson("Data/cleaned_tweets%s.txt" %year)
    load_in()
    actor_list = loadjson("Data/actor_list.txt")
    is_actor = False

    award_lis = []
    award_name = award.names
    reg = re.compile(r"(actor|actress|director|performance)")
    if re.search(reg, award_name):
        is_actor = True
    
    words = award_name.split()

    for i in range(len(words)):
        if i != 0:
            award_lis.append(" ".join(words[:i+1]))

    nom_tweets = get_nom_tweets(cleaned_tweet_data, award_lis)
    name_list = buildNameList(nom_tweets)
    if is_actor:
        names_dict = countNamesActor(name_list)
    else:
        names_dict = countNamesMovie(name_list)
    sorted_list = sorted(names_dict.items(), key = lambda kv: kv[1])

    if is_actor:
        final_noms_dict = actorCheck(actor_list, sorted_list)
    else:
        final_noms_dict = sorted_list
        
    final_list = []
    for element in final_noms_dict[-5:]:
        final_list.append([element[0], 0])

    award.Nominee = final_list

    buildConfidence(award, cleaned_tweet_data)
    get_winner(award)
    
    return 
