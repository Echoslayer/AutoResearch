# EDIT_FINAL_OUTLINE_PROMPT = '''
# You are an expert in artificial intelligence who wants to write a overall survey about [TOPIC].\n\
# You have created a draft outline below:\n\
# ---
# [OVERALL OUTLINE]
# ---
# The Total number of sections should be [TOTAL NUMBER OF SECTIONS]
# The outline contains a title and several sections.\n\
# Each section follows with a brief sentence to describe what to write in this section.\n\n\
# Under each section, there are several subsections.
# Each subsection also follows with a brief sentence of descripition.
# Some of the subsections may be repeated or overlaped.
# You need to modify the outline to make it both comprehensive and logically coherent with no repeated subsections.
# Repeated subsections among sections are not allowed!
# Return the final outline in the format:
# <format>
# # [TITLE OF SURVEY]

# ## [NAME OF SECTION 1]
# Description: [DESCRIPTION OF SECTION 1]
# ### [NAME OF SUBSECTION 1]
# Description: [DESCRIPTION OF SUBSECTION 1]
# ### [NAME OF SUBSECTION 2]
# Description: [DESCRIPTION OF SUBSECTION 2]
# ...

# ### [NAME OF SUBSECTION L]
# Description: [DESCRIPTION OF SUBSECTION L]
# ## [NAME OF SECTION 2]

# ...

# ## [NAME OF SECTION K]
# ...

# </format>
# Only return the final outline without any other informations:
# '''


EDIT_FINAL_OUTLINE_PROMPT='''
You are an expert in artificial intelligence who wants to write a overall survey about [TOPIC].\n\
You have created a draft outline below:\n\
---
[OVERALL OUTLINE]
---
The Total number of sections should be [TOTAL NUMBER OF SECTIONS]
The outline contains a title and several sections.\n\
Each section follows with a brief sentence to describe what to write in this section.\n\n\
Under each section, there are several subsections.
Each subsection also follows with a brief sentence of descripition.
Some of the subsections may be repeated or overlaped.
You need to modify the outline to make it both comprehensive and logically coherent with no repeated subsections.
Repeated subsections among sections are not allowed!
Return the final outline in the format:

<format>  
# [TITLE OF SURVEY]  

## [NAME OF SECTION]  
Description: [DESCRIPTION OF SECTION]  

### [NAME OF SUBSECTION]  
Description: [DESCRIPTION OF SUBSECTION]  

### [NAME OF SUBSECTION]  
Description: [DESCRIPTION OF SUBSECTION]  

...  

## [NAME OF SECTION]  

...

## [NAME OF SECTION]  
...  
</format>  

Only return the final outline without any numbering in the sections or subsections.
'''