 
 
# Sprint 1 Report  1/12/26 - 2/22/26
 ## YouTube link of Sprint 1 Video 
https://www.youtube.com/watch?v=UhXACyUTNCE

 ## What's New (User Facing)
 * Prompt sanitization based on RegEx scanning
 * LLM classification for prompt injection detection
 * Statistical outputs
* User interface
* Expanded dataset

 ## Work Summary (Developer Facing)
During this sprint, our team accomplished a basic sanitization function for prompt injections, reaching about 70% accuracy. The scanner includes flagging for pre-made regular expressions in the prompt and calls to a local LLM that determines whether or not the prompt contains a regular expression. We also created a prompt hardening template which is intended to separate potential unsanitized prompt injections from instructions to execute. Finally, we also created a poster for viceroy as a preliminary presentation of our work so far, which includes the background of our problem, examples of how our system should work, and an explanation of the mechanics behind our prototype.

 ## Unfinished Work
We completed everything we planned for this sprint.

 ## Completed Issues/User Stories
 Here are links to the issues that we completed in this sprint:
 * Initial User Interface
 * RegEx Scanning
 * Expand Dataset
 * Output statistics

 ## Incomplete Issues/User Stories
N/A

 ## Code Files for Review
 Please review the following code files, which were actively developed during this
 sprint, for quality:
*[Data_Sanitzation_Engine.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/Data_Sanitization_Engine.py) *[classifier.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/classifier.py
*[data.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/data.py)
*[detect.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/detect.py)
*[peformance_stats.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/performance_stats.py)
*[sanitize.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/sanitize.py)
*[run.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/flask-app/run.py)
*[routes.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/flask-app/app/routes.py)

 ## Retrospective Summary
 Here's what went well:
 * Creating working parts of a prototype
 * Completing the VICEROY poster
 Here's what we'd like to improve:
 * Connecting features together
 * Completing the LLM classification feature
 * Working in branches to make issue documentation (linking to pull requests) easier.

 Here are changes we plan to implement in the next sprint:
 * Connect the UI and data processing modules for complete flow through the prototype
 * Add additional systems for sanitization
 	* Sanitize prompts based on LLM classifier output.
 * Add additional systems for detection
 * Allow users to choose which LLM their sanitized input goes to.
## AI Disclosure
Used ChatGPT to help generate the initial template for the flask application user interface.
Used ChatGPT to help with Python functions/packages such as regular expression scanning and Ollama queries.

