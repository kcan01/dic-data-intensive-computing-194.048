import json
import heapq

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
        """ Only uncomment if needed
        self.add_passthru_arg(
            '--arg1',
            type=int,
            default=0,
            help='Add argument description here'
        )
        """
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
            self.stopwords = {line.strip().lower() for line in f}

    def mapper_init(self):
        """Initialize mapper state before processing any records."""
        # Dictionary to store term counts by category: {term1: {category1: count1, ...}, ...}
        self.term_category_counts = {}
        self.splitter = re.compile(r"[ \t\d(){}\[\].!?;:,+\-=\"~#@&*%€$§\\'\n\r]+")

    def mapper(self, _, line):
        """Process each document and count term occurrences by category.

        Args:
            _: Ignored key
            line: Input line containing a JSON document

        Note:
            Does not yield any values directly; accumulates counts in memory
            to be processed by mapper_final.
        """
        document = json.loads(line)
        category_id = self.categories_map.get(document['category'], "X")
        text = document['reviewText'].lower()

        for token in self.splitter.split(text):
            # Apply preprocessing here
            token = token.strip()

            if (len(token) <= 1) or (token in self.stopwords):
                continue

            if token not in self.term_category_counts:
                self.term_category_counts[token] = {}

            updated_count = self.term_category_counts.get(token, {}).get(category_id, 0) + 1
            self.term_category_counts[token][category_id] = updated_count

    def mapper_final(self):
        """Emit accumulated term counts after processing all records in a split.

        Yields:
            tuple: (term, {category_id: count, ...})
        """
        for term, term_count_dict in self.term_category_counts.items():
            yield term, term_count_dict

    def combiner(self, term, multiple_term_count_dicts):
        """Combine term count dictionaries from multiple mappers.

        Args:
            term: The term being counted
            multiple_term_count_dicts: Iterator of category count dictionaries

        Yields:
            tuple: (term, combined_counts)
        """
        combined_dict = {}
        for term_count_dict in multiple_term_count_dicts:
            # For each dictionary, add its values to the combined dictionary
            for category_id, count in term_count_dict.items():
                combined_dict[category_id] = combined_dict.get(category_id, 0) + count
        yield term, combined_dict

    def reducer_count(self, term, multiple_term_count_dicts):
        """Calculate chi-square statistic for each term-category pair.

        Args:
            term: The term being analyzed
            multiple_term_count_dicts: Iterator of category count dictionaries

        Yields:
            tuple: ((term, category), chi_square_value)
        """
        term_occurrences_per_category = {}
        # Calculate occurrence of term per category
        # Example {"action": 20, "romance": 3, ...}
        for term_count_dict in multiple_term_count_dicts:
            for category_id, count in term_count_dict.items():
                term_occurrences_per_category[category_id] = term_occurrences_per_category.get(category_id, 0) + count

        n_documents = sum(self.frequencies_dict.values())
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
            chi_square = N * (A*D - B*C)**2 / ((A+B)*(A+C)*(B+D)*(C+D))
            yield (term, category), chi_square

    def mapper_categories(self, key, chi_square):
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
            tuple: (category_name, output_string)
        """
        # Get the top 75 terms with highest chi-square values
        top_terms = heapq.nlargest(n=75, iterable=values, key=lambda x: x[1])

        yield category_id, top_terms

    def reducer_nlargest_chisq(self, category_id, values):
        """Find the top N terms with highest chi-square values for each category.

        Args:
            category_id: The category ID
            values: Iterator of (term, chi_square) pairs

        Yields:
            tuple: (category_name, output_string)
        """
        # Get the top 75 terms with highest chi-square values
        top_terms = heapq.nlargest(n=75, iterable=values, key=lambda x: x[1])

        yield category_id, top_terms

    def steps(self):
        """Define the MapReduce steps for this job."""
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper,
                mapper_final=self.mapper_final,
                combiner=self.combiner,
                reducer=self.reducer_count
            ),
            MRStep(
                mapper=self.mapper_categories,
                combiner=self.combiner_nlargest_chisq,
                reducer=self.reducer_nlargest_chisq
            )
        ]

    
if __name__ == '__main__':
    ChiSquareCalculator.run()
