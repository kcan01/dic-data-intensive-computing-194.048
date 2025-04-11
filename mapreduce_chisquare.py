
#Import necessary packages 
from mrjob.job import MRJob
from mrjob.step import MRStep
import json
import re


#-----------------------------
#-------------INPUT BEGINNING----------------------------

stopwords = 'stopwords.txt'


#-------------INPUT END---------------------

class MRChiSquare(MRJob):
    #read the necessary files 
    with open('stopwords.txt', 'r') as f:
        stopwords = f.read().split()
        
       # split data according to assignment 
    def mapper_init(self):
        with open(self.options.stopwords, 'r') as f:
            self.stopwords = set(word.strip().lower() for word in f if word.strip())
        self.splitter = re.compile(r"[ \t\d(){}\[\].!?;:,+\-=\"~#@&*%€$§\\'\n\r]+")

    def preprocess(self, text):
        text = text.lower()
        tokens = self.splitter.split(text)
        return [t for t in tokens if len(t) > 1 and t not in self.stopwords]

    def mapper(self, _, line):
        try:
            review = json.loads(line)
            category = review.get("category")
            text = review.get("reviewText", "")
            if not category or not text:
                return

            words = set(self.preprocess(text))
            yield ("__DOC_COUNT__", None), 1
            yield ("__DOC_CAT__", category), 1

            for word in words:
                yield (word, category), 1
                yield (word, "__TOTAL__"), 1
        except:
            pass
        
        #input is <(word, category), 1>, sum this up for faster execution
        def combiner(self, key, counts):
            word, category = key
            yield word, (category, sum(counts))
            
        #in reducer chi-square is performed 
        #input should be output of combiner 
        #so key is word, category and how sum of counts 
        #now to get total values we yielded __DOC_COUNT__ and _DOC_CAT__  und __TOTAL__ 
        #brauchen noch initialiser für: 
        #total amount of docs 
        #documents per category 
        #counts of word per category
        #total amount of terms?
        def reducer_init(self): 
            
        
        def reducer():

            

        def steps(self):
            return [MRStep(mapper_init = self.mapper_init,
                           mapper = self.mapper,
                           combiner = self.combiner,
                           reducer_init = self.reducer_init,
                           reducer = self.reducer)]
        
        
if __name__ == '__main__':
    MRChiSquare.run()  # where MRChiSquare is your job class
#Chi Square Formula 

#c = Category 
#t = term 

#N = total number of retrieved documents
#A = number of documents in c which contain t 
#B = number of documents not in c which contain t
#C = number of documents in c without t 
#D = number of documents not in c without t

#A + B + C + D should be N 


# oberer Term
# N (AD - BC)^2

#unterer Term 

# (A + B)(A + C)(B + D)(C + D)


if __name__ == '__main__':
    MRChiSquare.run()  # where MRChiSquare is your job class

