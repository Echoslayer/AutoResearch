# SUBSECTION_WRITING_PROMPT = '''
# You are an expert in artificial intelligence who wants to write a overall and comprehensive survey about [TOPIC].\n\
# You have created a overall outline below:\n\
# ---
# [OVERALL OUTLINE]
# ---
# Below are a list of papers for references:
# ---
# [PAPER LIST]
# ---

# <instruction>
# Now you need to write the content for the subsection:
# "[SUBSECTION NAME]" under the section: "[SECTION NAME]"
# The details of what to write in this subsection called [SUBSECTION NAME] is in this descripition:
# ---
# [DESCRIPTION]
# ---

# Here is the requirement you must follow:
# 1. The content you write must be more than [WORD NUM] words.
# 2. When writing sentences that are based on specific papers above, you cite the "paper_title" in a '[]' format to support your content. An example of citation: 'the emergence of large language models (LLMs) [Language models are few-shot learners; PaLM: Scaling language modeling with pathways]'
#     Note that the "paper_title" is not allowed to appear without a '[]' format. Once you mention the 'paper_title', it must be included in '[]'. Papers not existing above are not allowed to cite!!!
#     Remember that you can only cite the paper provided above and only cite the "paper_title"!!!
# 3. Only when the main part of the paper support your claims, you cite it.


# Here's a concise guideline for when to cite papers in a survey:
# ---
# 1. Summarizing Research: Cite sources when summarizing the existing literature.
# 2. Using Specific Concepts or Data: Provide citations when discussing specific theories, models, or data.
# 3. Comparing Findings: Cite relevant studies when comparing or contrasting different findings.
# 4. Highlighting Research Gaps: Cite previous research when pointing out gaps your survey addresses.
# 5. Using Established Methods: Cite the creators of methodologies you employ in your survey.
# 6. Supporting Arguments: Cite sources that back up your conclusions and arguments.
# 7. Suggesting Future Research: Reference studies related to proposed future research directions.
# ---

# </instruction>
# Return the content of subsection "[SUBSECTION NAME]" in the format:
# <format>
# [CONTENT OF SUBSECTION]
# </format>
# Only return the content more than [WORD NUM] words you write for the subsection [SUBSECTION NAME] without any other information:
# '''

# SUBSECTION_WRITING_PROMPT = """
# You are an expert in artificial intelligence writing a comprehensive survey about [TOPIC].

# Overall outline:
# [OVERALL OUTLINE]

# Reference papers:
# [PAPER LIST]

# Task: Write content for the subsection "[SUBSECTION NAME]" under the section "[SECTION NAME]".

# Subsection description:
# [DESCRIPTION]

# Instructions:
# 1. Write more than [WORD NUM] words for this subsection.
# 2. Cite papers using the following format: [paper_title]. Example: "Recent advancements in natural language processing [GPT-3: Language Models are Few-Shot Learners]"
# 3. Only cite papers from the provided list above.
# 4. Cite papers only when they directly support your claims or provide specific data/concepts.
# 5. Follow these citation guidelines:
#    a. Cite when summarizing existing literature.
#    b. Cite when discussing specific theories, models, or data.
#    c. Cite when comparing or contrasting findings.
#    d. Cite when highlighting research gaps.
#    e. Cite when using established methods.
#    f. Cite when supporting arguments.
#    g. Cite when suggesting future research directions.
# 6. Structure your content logically, using paragraphs to separate ideas.
# 7. Ensure your writing is clear, concise, and academic in tone.

# Output format:
# ---BEGIN SUBSECTION CONTENT---
# [Your subsection content here, following all the instructions above]
# ---END SUBSECTION CONTENT---

# Important: Strictly adhere to the format above. Do not include any text before or after the delimiters. Ensure your content is more than [WORD NUM] words and follows all citation guidelines.
# """

SUBSECTION_WRITING_PROMPT = """
You are an expert in artificial intelligence writing a comprehensive survey about [TOPIC].

Overall outline:
[OVERALL OUTLINE]

Reference papers:
[PAPER LIST]

Task: Write content for the subsection "[SUBSECTION NAME]" under the section "[SECTION NAME]".

Subsection description:
[DESCRIPTION]

Instructions:
1. Write more than [WORD NUM] words for this subsection.
2. Cite papers using the following format: [paper_title]. Example: "Recent advancements in natural language processing [GPT-3: Language Models are Few-Shot Learners]"
3. Only cite papers from the provided list above.
4. Cite papers only when they directly support your claims or provide specific data/concepts.
5. Follow these citation guidelines:
   a. Cite when summarizing existing literature.
   b. Cite when discussing specific theories, models, or data.
   c. Cite when comparing or contrasting findings.
   d. Cite when highlighting research gaps.
   e. Cite when using established methods.
   f. Cite when supporting arguments.
   g. Cite when suggesting future research directions.
6. Structure your content logically, using paragraphs to separate ideas.
7. Ensure your writing is clear, concise, and academic in tone.

Output the content in the following JSON format:

{
  "subsection_name": "[SUBSECTION NAME]",
  "section_name": "[SECTION NAME]",
  "content": "Your subsection content here, following all the instructions above. Ensure this content is more than [WORD NUM] words and follows all citation guidelines.",
  "word_count": 0,
  "citations": [
    {"paper_title": "Title of Paper 1", "count": 0},
    {"paper_title": "Title of Paper 2", "count": 0}
  ]
}

Important: 
1. The JSON should be valid and properly formatted.
2. Replace the placeholder text in the "content" field with your actual subsection content.
3. Update the "word_count" field with the actual word count of your content.
4. In the "citations" array, include only the papers you've cited, with their correct titles and citation counts.
5. Ensure your content is more than [WORD NUM] words and follows all citation guidelines.
6. Do not include any text or explanation outside of this JSON structure.
"""