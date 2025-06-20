import os
import shutil

def prune_nltk_data(base_path="package/nltk_data"):
    # Keep only english.pickle in punkt tokenizer
    punkt_path = os.path.join(base_path, "tokenizers", "punkt")
    for file in os.listdir(punkt_path):
        if file.endswith(".pickle") and file != "english.pickle":
            os.remove(os.path.join(punkt_path, file))

    punkt_path = os.path.join(base_path, "tokenizers", "punkt_tab")
    for folder in os.listdir(punkt_path):
        folder_path = os.path.join(punkt_path, folder)
        if folder != "english" and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)

    # Keep only 'english' stopwords directory
    stopwords_path = os.path.join(base_path, "corpora", "stopwords")
    for file in os.listdir(stopwords_path):
        if file != "english":
            os.remove(os.path.join(stopwords_path, file))

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".zip") and file!="wordnet.zip":
                os.remove(os.path.join(root, file))
            
if __name__=="__main__":
    prune_nltk_data()


