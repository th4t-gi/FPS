import time
t = time.time()
from nltk.tokenize import word_tokenize
from gensim.models import Word2Vec
from sklearn.decomposition import PCA
from matplotlib import pyplot
from collections import namedtuple, OrderedDict
import subprocess, re, os, numpy as np, random, string, warnings

#finds the directory path of given folder
def find_packet(file, rootdir="~/", dir=True):
    if dir: d = "d"
    else: d = "f"
    try:
        _packet_path = subprocess.check_output("find {} -type {} -name \"{}\"".format(rootdir, d, file),shell=True,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _packet_path = e.output
    if not _packet_path.endswith("/"):
        _packet_path = _packet_path.replace('\n', '')
    return _packet_path

class packet(object):

    def __init__(self, *args):
        super(packet, self).__init__()
        self.packets = flatten(args)
        self.packets = list(set(flatten([self.get_packets(i) for i in self.packets])))
        self.paths = [self.get_data(i) for i in self.packets]
        self.paths = [j for i in self.paths for j in i if not j == "NO PACKET"]

    def get_data(self, packet):
        self.packet = packet
        if not self.packet:
            return ["NO PACKET"]
        self.requested_packet = not(self.packet.lower() == "all")
        self.packet = self.packet.upper()
        self.flashdrive = "no" #raw_input("Is the packet {} on a USB drive?(yes/no): ".format(self.packet))

        if self.flashdrive == "yes":
            self.flashdrive = raw_input("What is the name of the USB drive?: ")
            if self.flashdrive.lower() in [item.lower() for item in os.listdir("/Volumes")]:
                os.chdir("/Volumes/{}".format(self.flashdrive))
                paths = find_packet(packet, os.getcwd())
        #finds path to given packet, or all packets
        try:
            self.data = find_packet(self.packet, "~/Code/")
            isda = self.isdata(self.packet)
            if not isda:
                return ["NO PACKET"]
            self.data = ''.join(re.split(re.compile(r"({})".format(self.packet)), self.data)[:2]) + "/"
            self.data = [self.data + i for i in os.listdir(self.data) if 'data' in i]
            print "\033[1mFound Packet:\033[0m", self.packet
        except subprocess.CalledProcessError as e:
            self.data = e.output
        except OSError:
            print "invalid packet directory: {}".format(self.packet)
            quit()
        try:
            return self.data
        except IndexError:
            print "packet file(s) not found"

    def get_packets(self, packet):
        if packet == "ALL":
            paths = subprocess.check_output("find ~/Code/ -regex \".*/data-[^score].*\.json\" -type f",shell=True,stderr=subprocess.STDOUT)
            paths = [i for i in paths.split("\n") if i and os.path.basename(os.path.dirname(i)) not in self.packets]
            packet = [os.path.basename(os.path.dirname(i)) for i in paths]
        return packet

    def isdata(self, p):
        if not self.data:
            print "\033[91m{}\033[0m is not an FPS packet".format(str(p))
            return False
        else: return True


class categorizedData(object):

    def __init__(self, data, vecs):
        super(categorizedData, self).__init__()
        self.gp = ["categories", "perhaps", "why", "duplicate", "solution"]
        #finds text from data obj
        self.tokens = tokenize(data["packet"]["text"], single=True)
        self.words = " ".join(self.tokens)
        # #finds categories for the self.tokens
        self.category = [tup for tup in data["scoring"].items() if tup[0] in self.gp]
        self.category = [tup for tup in self.category if tup[1]][0]
        if self.category[0] == "categories": self.category = self.category[1]
        else: self.category = self.category[0]
        #combines self.tokens and self.categorys
        self.vecs = [vecs[token] for token in self.tokens]
        self.v = OrderedDict(zip(self.tokens, self.vecs))

def getData(key, dictionary, track=False):
    for k, v in dictionary.iteritems():
        if re.match(key, k): yield v
        elif isinstance(v, dict):
            for result in getData(key, v):
                yield result
        elif isinstance(v, list):
            for i, d in enumerate(v):
                if track:
                    yield i
                if type(d) == dict:
                    for result in getData(key, d): yield result

def vectorize(l, show=False, size=100, sim=[]):
    warnings.simplefilter(action="ignore", category=FutureWarning)
    # train model
    model = Word2Vec(l, min_count=1, size=size)
    X = model[model.wv.vocab]
    words = [word for word in list(model.wv.vocab) if word]
    formatted = dict(zip(words, X))
    if sim and len(sim) in [2, 3]:
        if len(sim) == 2:
            result = model.most_similar(positive=[sim[0]], negative=[sim[1]], topn=5)
        else:
            result = model.most_similar(positive=[sim[0], sim[2]], negative=[sim[1]], topn=5)
        print result
    if show:
        # create a scatter plot of the projection
        pca = PCA(n_components=2)
        result = pca.fit_transform(X)
        pyplot.scatter(result[:, 0], result[:, 1])
        words = list(model.wv.vocab)
        for i, word in enumerate(words):
        	pyplot.annotate(word, xy=(result[i, 0], result[i, 1]))
        pyplot.show()

    return formatted


def tokenize(text, single=False):
    if single:
        tokens = word_tokenize(text.replace("/", " ").replace("\"", ""))
        return [word.lower() for word in tokens if not word.lower() in string.punctuation if not "'" in word]
    if not type(text[0]) == list:
        raise TypeError("Text must be nested list of strings, not list of type str")
    tokens = [[word_tokenize(i.replace("/", " ").replace("\"", "")) for i in packet] for packet in text]
    return [[[word.lower() for word in i if not word.lower() in string.punctuation if not "'" in word] for i in packet] for packet in tokens]

def flatten(l, iter=float("inf")):
    result = []
    for el in l:
        if iter == 0:
            result.append(l)
            break
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el, iter - 1))
        else: result.append(el)
    return result

def ask(ask):
    while True:
        result = raw_input(ask)
        if result == "" or result == "ALL": yield result; break
        else: yield result; continue

# print "time:", round(timeself.time()- t, 3)