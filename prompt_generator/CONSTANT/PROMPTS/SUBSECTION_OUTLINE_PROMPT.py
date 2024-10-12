# SUBSECTION_OUTLINE_PROMPT = '''
# You are an expert in artificial intelligence who wants to write a overall survey about [TOPIC].\n\
# You have created a overall outline below:\n\
# ---
# [OVERALL OUTLINE]
# ---
# The outline contains a title and several sections.\n\
# Each section follows with a brief sentence to describe what to write in this section.\n\n\
# <instruction>
# You need to enrich the section [SECTION NAME].
# The description of [SECTION NAME]: [SECTION DESCRIPTION]
# You need to generate the framework containing several subsections based on the overall outlines.\n\
# Each subsection follows with a brief sentence to describe what to write in this subsection.
# These papers provided for references:
# ---
# [PAPER LIST]
# ---
# Return the outline in the format:
# <format>
# Subsection 1: [NAME OF SUBSECTION 1]
# Description 1: [IMPROVED DESCRIPTION OF SUBSECTION 1]

# Subsection 2: [NAME OF SUBSECTION 2]
# Description 2: [IMPROVED DESCRIPTION OF SUBSECTION 2]

# Subsection 3: [NAME OF SUBSECTION 3]
# Description 3: [IMPROVED DESCRIPTION OF SUBSECTION 3]

# [Continue with additional subsections as needed]
# </format>
# </instruction>
# Only return the outline without any other information.
# '''

SUBSECTION_OUTLINE_PROMPT = """
You are an expert in artificial intelligence writing a survey about [TOPIC].

Overall outline:
[OVERALL OUTLINE]

Task: Enrich the section "[SECTION NAME]".
Section description: [SECTION DESCRIPTION]

Generate a framework with several subsections based on the overall outline. Each subsection should have a name and a brief description.

Reference papers:
[PAPER LIST]

Instructions:
1. Create subsections for the "[SECTION NAME]" section.
2. Provide a name and description for each subsection.
3. Follow the exact format shown below.
4. Do not include any additional text or explanations outside the specified format.

Output format:
---BEGIN OUTPUT---
Subsection 1: [NAME OF SUBSECTION 1]
Description 1: [DESCRIPTION OF SUBSECTION 1]

Subsection 2: [NAME OF SUBSECTION 2]
Description 2: [DESCRIPTION OF SUBSECTION 2]

Subsection 3: [NAME OF SUBSECTION 3]
Description 3: [DESCRIPTION OF SUBSECTION 3]

[Continue with additional subsections as needed]
---END OUTPUT---

Strictly adhere to the format above. Do not include any text before or after the delimiters.
"""