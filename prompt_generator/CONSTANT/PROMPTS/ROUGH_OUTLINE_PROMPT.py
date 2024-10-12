ROUGH_OUTLINE_PROMPT = '''
You wants to write a overall and comprehensive academic survey about "[TOPIC]".\n\
You are provided with a list of papers related to the topic below:\n\
---
[PAPER LIST]
---
You need to draft a outline based on the given papers.
The outline should contains a title and several sections.
Each section follows with a brief sentence to describe what to write in this section.
The outline is supposed to be comprehensive and contains [SECTION NUM] sections.

Return in the format:
<format>
Title: [TITLE OF THE SURVEY]
Section 1: [NAME OF SECTION 1]
Description 1: [DESCRIPTION OF SENTCTION 1]

Section 2: [NAME OF SECTION 2]
Description 2: [DESCRIPTION OF SENTCTION 2]

...

Section K: [NAME OF SECTION K]
Description K: [DESCRIPTION OF SENTCTION K]
</format>
The outline:
'''
