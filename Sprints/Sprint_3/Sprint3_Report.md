# Sprint 3 Report (03/24/26 to 05/01/26)
## YouTube link of Sprint 3 Video 
https://www.youtube.com/watch?v=KOLqENuH37U

## What's New (User Facing)
* Data detection/sanitization engine connected to UI
* UI batch file upload and parsing
* Output validation module
* Improved regular expression robustness
## Work Summary (Developer Facing)
Our team added finishing touches to our originally collected functional requirements. Once finished, our team entered an exploratory phase to figure out which direction to take this project. To face this issue, our team met up with our mentor, Tashi, and each decided on a new direction of research to take on the project. We hope to develop a new set of requirements and features for the upcoming semester.

## Unfinished Work
Our team was successful in completing our original requirements. Unfinished work includes identifying where our current pipeline is lacking, but this is an ongoing challenge as we are in an open-problem space of prompt injection mitigation.

We believe that our testing suite still has room for improvement to ensure that our systems are as robust as possible.

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/17
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/18
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/16

## Incomplete Issues/User Stories
N/A
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* Data_Sanitization_Engine.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/Data_Sanitization_Engine.py
* sanitize.py : https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/sanitize.py
* base.html : https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/flask-app/app/templates/base.html
* routes.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/flask-app/app/routes.py
* api_call.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/api_call.py
*prompt_hardening.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/prompt_hardening.py
## Retrospective Summary
Here's what went well:
* Implemented full data pipeline and connected to UI
* Expanded dataset to better generalize to problem
Here's what we'd like to improve:
* Overall testing robustness
* Improving and expanding the token vectorization strategy for detection 
Here are changes we plan to implement in the next sprint:
* Exploratory data analysis on current detection edge cases
* Explore different media types such as image, video, audio

