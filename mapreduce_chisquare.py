
#Import necessary packages 
from mrjob.job import MRJob
from mrjob.step import MRStep
import json
import re
from collections import defaultdict



#-----------------------------
#-------------INPUT BEGINNING----------------------------


#-------------INPUT END---------------------

class MRChiSquare(MRJob):
    #read the necessary files 
    def configure_args(self):
        super().configure_args()
        self.add_file_arg('--stopwords')
        
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
        self.total_docs = 0
        self.docs_per_cat = defaultdict(int)
        self.term_cat_counts = defaultdict(lambda: defaultdict(int))
        self.term_totals = defaultdict(int)
    
    #key is (word, category)
    def reducer(self,key, values):
        word, category = key
        #if word = DOC_COUNT then summarize all values 
        if word == "__DOC_COUNT__":
            self.total_docs += sum(values)
        #otherwise if we want number of documents per cat 
        #summarize documents per category
        elif word == "__DOC_CAT__":
            self.docs_per_cat[category] += sum(values)
        #next case is if we want to count total number of terms 
        elif category == "__TOTAL__":
            self.term_totals[word] += sum(values)
        else:
            #now  we want to count occurance per term and category
            self.term_cat_counts[word][category] += sum(values)
    
    def reducer_final(self):
        chi_sq_results = defaultdict(list)

        for term, cat_counts in self.term_cat_counts.items():
            for cat in self.docs_per_cat:
                A = cat_counts.get(cat, 0)  # number of documents in c which contain t 
                B = self.term_totals[term] - A  # number of documents not in c which contain t
                C = self.docs_per_cat[cat] - A  # number of documents in c without t 
                D = self.total_docs - A - B - C  # number of documents not in c without t

                numerator = self.total_docs * (A * D - B * C) ** 2
                denominator = (A + B)*(A + C)*(B + D)*(C + D) if (A + B)*(A + C)*(B + D)*(C + D) > 0 else 1
                chi2 = numerator / denominator
                chi_sq_results[cat].append((term, chi2))

            # only give top 75 terms per category
        merged_terms = set()
        for cat in sorted(chi_sq_results):
            top_terms = sorted(chi_sq_results[cat], key=lambda x: x[1], reverse=True)[:75]
            line = " ".join([f"{term}:{round(score, 3)}" for term, score in top_terms])
            yield cat, line
            for term, _ in top_terms:
                merged_terms.add(term)

        # Letzte Zeile: alphabetisch sortiertes Dictionary
        final_dict = " ".join(sorted(merged_terms))
        yield "__Dictionary__", final_dict

    def steps(self):
        return [MRStep(mapper_init = self.mapper_init,
                          mapper = self.mapper,
                          combiner = self.combiner,
                          reducer_init = self.reducer_init,
                          reducer = self.reducer,
                          reducer_final = self.reducer_final)]
        
        
if __name__ == '__main__':
    MRChiSquare.run()  
    
    
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



