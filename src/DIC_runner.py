# runner script to run the Chi Square Calculator

import logging
logging.basicConfig(filename='DICrunner.log', level=logging.INFO)
logging.getLogger('mrjob').setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from tempfile import NamedTemporaryFile
from categorycounter import CategoryCounter
from chisquarecalculator import ChiSquareCalculator
import json
import sys, os
from timeit import default_timer as timer




if __name__ == '__main__':
    starttime = timer()
    dict_file_path = 'categories.json'
    stopwords_file_path = 'stopwords.txt'
    category_frequencies = {}

    with open(dict_file_path) as f:
        categories_map = json.load(f)
    all_categories = {id: name for name, id in categories_map.items()}


    logger.info(f'Loaded {len(all_categories)} categories successfully from {dict_file_path}')
    elapsed_time = timer() - starttime
    logger.info(f'--- Elapsed time {elapsed_time:.3f} seconds ({(elapsed_time / 60):.2f} min)')

    # Pipe through and extend command line args 
    categoryCounterArgs = [
        f'--category_dict_file={dict_file_path}',
        ]
    categoryCounterArgs.extend(sys.argv[1:])

    categoryCounterJob = CategoryCounter(args=categoryCounterArgs)
    with categoryCounterJob.make_runner() as runner:
        runner.run()
        for key, value in categoryCounterJob.parse_output(runner.cat_output()):
            category_frequencies[key] = int(value)

    logger.info(f'--- Ran CategoryCounter Job successfully')
    elapsed_time = timer() - starttime
    logger.info(f'--- Elapsed time {elapsed_time:.3f} seconds ({(elapsed_time / 60):.2f} min)')

    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(category_frequencies, f)
        category_frequencies_path = f.name

    logger.info(f'Dumped results into temporary file')

    # Pipe through and extend command line args 
    chisquareCalculatorArgs = [
        #'--arg1', str(threshold_value), #commented out since not implemented
        f'--category_dict_file={dict_file_path}',
        f'--category_frequencies_file={category_frequencies_path}',
        f'--stopword_file={stopwords_file_path}',
        ]
    chisquareCalculatorArgs.extend(sys.argv[1:])


    job = ChiSquareCalculator(args=chisquareCalculatorArgs)
    with job.make_runner() as runner:
        runner.run()

        for category_id, top_term_list in job.parse_output(runner.cat_output()):
            # Format output as "category_name term1:chi_square term2:chi_square ..."
            category_name = all_categories[category_id]

            output_str = category_name + " "

            output_str += " ".join([f'{term}:{chisq}' for term, chisq in top_term_list])

            print(output_str)

    logger.info(f'--- Ran ChiSquareCalculator Job successfully')
    elapsed_time = timer() - starttime
    logger.info(f'--- Elapsed time {elapsed_time:.3f} seconds ({(elapsed_time / 60):.2f} min)')



    # delete temp file
    os.unlink(category_frequencies_path)

