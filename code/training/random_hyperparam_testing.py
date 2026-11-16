# Train the random forest sentence classifiers used by sanitizer/detection/rf.py. From the code/ directory run:
# Run hyperparameter testing on random forest classifiers. From code/ directory run:
#     python training/random_hyperparam_testing.py                       # both models on dataset v2
#     python training/random_hyperparam_testing.py --dataset v1 --mode malicious    #Malicious model on dataset v1
# Results of testing are saved to code/results/.
# This one can take a long while, and will use all available resouces.
import argparse
import os
import numpy

from pandas import read_csv
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "results")
NGRAMMIN = 1
NGRAMMAX = 3

# imperative: subtype_id (0 = not imperative, 1 = benign imperative, 2 = malicious), with every value > 0 treated as 1
# malicious: label (0 = benign, 1 = prompt injection)
MODES = {
    "imperative": (lambda df: (df["subtype_id"] > 0).astype(int)),
    "malicious": (lambda df: df["label"]),
}

# Number of trees in random forest
N_ESTIMATORS = [int(x) for x in numpy.linspace(start = 200, stop = 2000, num = 10)]
# Number of features to consider at every split
MAX_FEATURES = ['auto', 'sqrt']
# Maximum number of levels in tree
MAX_DEPTH= [int(x) for x in numpy.linspace(10, 110, num = 11)]
MAX_DEPTH.append(None)
# Minimum number of samples required to split a node
MIN_SAMPLES_SPLIT = [2, 5, 10]
# Minimum number of samples required at each leaf node
MAX_SAMPLES_LEAF = [1, 2, 4]
# Method of selecting samples for training each tree
BOOTSTRAP = [True, False]


def train(dataFrame, mode, dataset):
    getLabels = MODES[mode]
    sentenceList = dataFrame["text"].tolist()
    labelList = getLabels(dataFrame).tolist()

    XTrain, XTest, YTrain, YTest = train_test_split(sentenceList, labelList, test_size=.2, random_state=10)

    # Create the random grid
    random_grid = {'n_estimators': N_ESTIMATORS,
               'max_features': MAX_FEATURES,
               'max_depth': MAX_DEPTH,
               'min_samples_split': MIN_SAMPLES_SPLIT,
               'min_samples_leaf': MAX_SAMPLES_LEAF,
               'bootstrap': BOOTSTRAP}

    NGramWordVectorizer = TfidfVectorizer(
        analyzer='word',
        ngram_range=(NGRAMMIN, NGRAMMAX)
        #consider turning on sublinear tf and comparing
        #sublinear_tf=True
    )
    
    RandomForestHolder = RandomForestClassifier()

    randomTuner = RandomizedSearchCV(
            estimator=RandomForestHolder,
            param_distributions=random_grid,
            n_iter = 100,
            cv = 3,
            verbose = 10,
            random_state=42,
            n_jobs= -1
    )

    hyperParamModel = Pipeline([('tfidf', NGramWordVectorizer), ('classifier', randomTuner)])

    hyperParamModel.fit(XTrain, YTrain)

    print(randomTuner.best_params_)

    with open(os.path.join(RESULTS_DIR, f"randomSearchResults_{mode}_{dataset}.txt"), 'w') as f:
        f.write(f"Optimal parameters for {mode} model on {dataset} dataset according to randomised search:\n")
        f.write(randomTuner.best_params_ + '\n')


def main():
    parser = argparse.ArgumentParser(description="Train the RF sentence classifiers.")
    parser.add_argument("--dataset", choices=["v1", "v2"], default="v2",
                        help="training/injection_detector_dataset<version>.csv to train on (default: v2)")
    parser.add_argument("--mode", choices=["imperative", "malicious", "both"], default="both",
                        help="which model to train (default: both)")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)

    dataFrame = read_csv(os.path.join(SCRIPT_DIR, f"injection_detector_dataset{args.dataset}.csv"))
    print("Data Loading Complete")

    modes = ["imperative", "malicious"] if args.mode == "both" else [args.mode]
    for mode in modes:
        train(dataFrame, mode, args.dataset)


if __name__ == "__main__":
    main()
