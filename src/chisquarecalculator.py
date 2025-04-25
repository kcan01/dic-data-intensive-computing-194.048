import json
import heapq
import logging
import re

from mrjob.job import MRJob
from mrjob.step import MRStep

class ChiSquareCalculator(MRJob):
    """MapReduce job for chi-square analysis of terms across document categories.

    This job processes documents to find the most statistically significant terms
    for each category based on chi-square analysis. It calculates the chi-square
    value for each term-category pair and returns the top N terms for each category.
    """

    def configure_args(self):
        """Configure command-line arguments for the job."""
        super(ChiSquareCalculator, self).configure_args()
        self.add_file_arg(
            '--category_dict_file',
            help='Path to JSON file containing category -> ID mapping'
        )
        self.add_file_arg(
            '--category_frequencies_file',
            help='Path to temporary JSON file containing category ID -> frequency mapping'
        )
        self.add_file_arg(
            '--stopword_file',
            help='Path to file containing stopwords (one per line)'
        )


    def load_args(self, args=None):
        """Load dictionaries and configuration from specified files."""
        super(ChiSquareCalculator, self).load_args(args)

        with open(self.options.category_dict_file) as f:
            self.categories_map = json.load(f)

        with open(self.options.category_frequencies_file) as f:
            self.frequencies_dict = json.load(f)

        with open(self.options.stopword_file, 'r', encoding='utf-8') as f:
            # Strip whitespace and convert to lowercase
            self.stopwords = {line.strip() for line in f}

        # Pre-compile regex pattern once
        self.splitter = re.compile(r"[ \t\d(){}\[\].!?;:,+\-=\"~#@&*%€$§\\'\n\r\/]+")

        # Cache total document count
        self.total_documents = sum(self.frequencies_dict.values())

    def mapper_count(self, _, line):
        """Process each document and emit term-category counts directly.

        Args:
            _: Ignored key
            line: Input line containing a JSON document

        Yields:
            tuple: ((term, category_id), 1) for each valid term
        """
        document = json.loads(line)
        category_id = self.categories_map.get(document['category'], "X")
        text = document['reviewText'].lower()

        # Process and emit term counts in batches
        tokens_all = set(self.splitter.split(text))
        tokens_all = tokens_all.difference(self.stopwords)

        for token in tokens_all:
            if len(token) > 1:
                yield (token, category_id), 1


    def combiner_count(self, key, counts):
        """Combine counts for the same term-category pair.

        Args:
            key: Tuple of (term, category_id)
            counts: Iterator of counts

        Yields:
            tuple: ((term, category_id), sum_of_counts)
        """
        yield key, sum(counts)

    def reducer_count(self, key, counts):
        """Calculate term frequencies.

        Args:
            key: Tuple of (term, category_id)
            counts: Iterator of counts

        Yields:
            tuple: (term, (category_id, count)) for all terms
        """
        term, category_id = key
        total_count = sum(counts)


        yield term, (category_id, total_count)

    def reducer_calc_chisq(self, term, category_counts):
        """Calculate chi-square statistic for each term-category pair.

        Args:
            term: The term being analyzed
            category_counts: List of tuples (category_id, count) for all categories

        Yields:
            tuple: ((term, category), chi_square_value)
        """
        # Calculate occurrence of term per category
        # Example {"action": 20, "romance": 3, ...}

        # Calculate total occurrences of this term across all categories
        term_occurrences_per_category = {cat: count for cat, count in category_counts}

        n_documents = self.total_documents
        n_documents_containing_term = sum(term_occurrences_per_category.values())

        for category, category_frequency in self.frequencies_dict.items():
            n_documents_in_cat = category_frequency

            # Calculate contingency table values for chi-square test
            n_documents_in_cat_containing_term = term_occurrences_per_category.get(category, 0)
            n_documents_not_in_cat_containing_term = n_documents_containing_term - n_documents_in_cat_containing_term
            n_documents_in_cat_not_containing_term = n_documents_in_cat - n_documents_in_cat_containing_term
            n_documents_not_in_cat_not_containing_term = (n_documents
                                                          - n_documents_in_cat
                                                          - n_documents_not_in_cat_containing_term)

            # Chi-square contingency table cells
            A = n_documents_in_cat_containing_term
            B = n_documents_not_in_cat_containing_term
            C = n_documents_in_cat_not_containing_term
            D = n_documents_not_in_cat_not_containing_term
            N = n_documents

            # Chi-square formula
            denominator = ((A+B)*(A+C)*(B+D)*(C+D))
            if denominator==0: continue

            chi_square = N * (A*D - B*C)**2 / denominator
            yield (term, category), chi_square

    def mapper_nlargest_chisq(self, key, chi_square):
        """Group chi-square values by category.

        Args:
            key: Tuple of (term, category_id)
            chi_square: Chi-square value for the term-category pair

        Yields:
            tuple: (category_id, (term, chi_square))
        """
        term, category_id = key
        yield category_id, (term, chi_square)

    def combiner_nlargest_chisq(self, category_id, values):
        """Find the top N terms with highest chi-square values for each category.

        Args:
            category_id: The category ID
            values: Iterator of (term, chi_square) pairs

        Yields:
            tuple: (category_id, (term, chi_square))
        """
        # Get the top 75 terms with highest chi-square values
        values = list(values)
        top_terms = heapq.nlargest(n=75, iterable=values, key=lambda x: x[1])

        for item in top_terms:
            yield category_id, item

    def reducer_nlargest_chisq(self, category_id, values):
        """Find the top N terms with highest chi-square values for each category.

        Args:
            category_id: The category ID
            values: Iterator of (term, chi_square) pairs

        Yields:
            tuple: (category_id, output list)
        """
        # Get the top 75 terms with highest chi-square values
        values = list(values)

        top_terms = heapq.nlargest(n=75, iterable=values, key=lambda x: x[1])

        yield category_id, top_terms

    def steps(self):
        """Define the MapReduce steps for this job."""
        return [
            MRStep(
                mapper=self.mapper_count,
                combiner=self.combiner_count,
                reducer=self.reducer_count
            ),
            MRStep(
                mapper=None,  # this step needs no mapper
                reducer=self.reducer_calc_chisq
            ),
            MRStep(
                mapper=self.mapper_nlargest_chisq,
                combiner=self.combiner_nlargest_chisq,
                reducer=self.reducer_nlargest_chisq
            )
        ]

    
if __name__ == '__main__':
    ChiSquareCalculator.run()
