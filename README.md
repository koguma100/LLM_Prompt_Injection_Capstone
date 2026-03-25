# Sanitizing Inputs to Protect LLMs Against Prompt Injection Attacks

## Project summary

Researching and testing sanitization techniques for mitigated prompt injections through poisoned data assuming trusted user prompts.

In positions where users – researchers, professors, and recruiters – take in large amounts of data for LLM analysis, prompt injections can stay hidden among a breadth of benign data. Our solution gives the user trust that the data they provide an LLM for processing will be sanitized of any prompt injections that could compromise internal systems.

## Installation

### Prerequisites

### This project requires Python and several packages listed in code/requirements.txt:

    requests
    scikit-learn
    matplotlib
    scipy
    numpy
    flask
    ollama

### Add-ons (Python packages)

    Requests: making http requests to local LLMs
    Scikit-learn: statistical outputs for testing detection performance
    Matplotlib: plotting the confusion matrix
    Scipy: delivers functions for computing the confusion matrix.
    Numpy: general math operations
    Flask: python web framework
    Ollama: locally run open-source LLMs

### Installation Steps

For running the Data_Sanitization_Engine.py, run:

    pip install -r requirements.txt (in code directory)

For running the Flask app install:

Flask, Ollama, Ollama model of choice (modify code)

Then run:

    python run.py

Future development will provide a Dockerfile to bypass manually entering the above steps.

## Functionality

In the locally hosted web page, enter a prompt for the LLM and the accompanying data. Note that these fields are separated, and only the “data” field will be processed. Once you have submitted, the Python backend will detect the data according to several regular expressions representative of prompt injections and with the response of an LLM classifier. Then, parts of the data determined to be prompt injections are removed and replaced with “[REDACTED]”. 

## Known Problems

We are unaware of any current problems with the code, as our scope for this sprint was limited and focused on creating a functioning prototype.

## Contributing 
Fork it!
Create your feature branch: git checkout -b my-new-feature
Commit your changes: git commit -am 'Add some feature'
Push to the branch: git push origin my-new-feature
Submit a pull request :D

## Additional Documentation
Project reports: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/tree/main/reports  
Sprint reports: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/tree/main/Sprints/Sprint_1    
Sprint 1 pull request: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/pull/10  
Sprint 1 pull request video: https://wsu.zoom.us/rec/share/0dqRWFE30yrMnKyMNyMjd4nvKxuI-D_gxhyytnGQioeWmv-1y3U__Shh_RxpBaL0.n-NPeKLvAUt2-DXt?startTime=1771812736000  
Poster submitted for VICEROY Symposium: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/Sprints/Sprint_2/Final_Poster_VICEROY_Symposium.png

## License

MIT License

