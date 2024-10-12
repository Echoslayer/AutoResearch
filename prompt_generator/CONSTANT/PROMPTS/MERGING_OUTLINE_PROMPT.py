MERGING_OUTLINE_PROMPT = '''
You are an expert in artificial intelligence who wants to write a overall survey about [TOPIC].\n\
You are provided with a list of outlines as candidates below:\n\
---
[OUTLINE LIST]
---
The Total number of sections should be [TOTAL NUMBER OF SECTIONS]
Each outline contains a title and several sections.
Each section follows with a brief sentence to describe what to write in this section.
You need to generate a final outline based on these provided outlines to make the final outline show comprehensive insights of the topic and more logical.
Return the in the format:
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
Only return the final outline without any other informations:
'''
