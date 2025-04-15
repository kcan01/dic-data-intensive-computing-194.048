import json

from mrjob.job import MRJob
from mrjob.step import MRStep

class CategoryCounter(MRJob):
    """MapReduce job to count documents by their category.

    This job reads documents in JSON format, extracts the category of each document,
    and counts how many documents belong to each category. Categories are converted
    to numeric IDs using a provided mapping file.
    """

    def configure_args(self):
        """Configure command-line arguments for the job."""
        super(CategoryCounter, self).configure_args()
        self.add_file_arg(
            '--category_dict_file',
            help='Path to JSON file containing category -> ID mapping'
        )

    def load_args(self, args=None):
        """Load category ID dictionary from the specified file."""
        super(CategoryCounter, self).load_args(args)
        with open(self.options.category_dict_file) as f:
            self.categories_dict = json.load(f)

    def mapper(self, _, line):
        """Extract category from each document and emit (category_id, 1).

        Args:
            _: Ignored key
            line: Input line containing a string JSON document

        Yields:
            tuple: (category_id, 1) for each document
        """
        document = json.loads(line)
        category = document['category']
        category_id = self.categories_dict[category]
        yield category_id, 1

    def combiner(self, category_id, counts):
        """Combine counts for the same category within a mapper.

        Args:
            category_id: The ID of the category
            counts: Iterator of counts (all 1s from mapper)

        Yields:
            tuple: (category_id, sum of counts)
        """
        yield category_id, sum(counts)

    def reducer(self, category_id, counts):
        """Reduce counts for the same category across all mappers.

        Args:
            category_id: The ID of the category
            counts: Iterator of partial sums from combiners

        Yields:
            tuple: (category_id, total count)
        """
        yield category_id, sum(counts)

    def steps(self):
        """Define the MapReduce steps for this job."""
        return [
            MRStep(
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer
            )
        ]

if __name__ == '__main__':
    CategoryCounter.run()