CHECK_CITATION_PROMPT = '''
You are an expert in artificial intelligence who wants to write a overall and comprehensive survey about [TOPIC].\n\
Below are a list of papers for references:
---
[PAPER LIST]
---
You have written a subsection below:\n\
---
[SUBSECTION]
---
<instruction>
The sentences that are based on specific papers above are followed with the citation of "paper_title" in "[]".
For example 'the emergence of large language models (LLMs) [Language models are few-shot learners; Language models are unsupervised multitask learners; PaLM: Scaling language modeling with pathways]'

Here's a concise guideline for when to cite papers in a survey:
---
1. Summarizing Research: Cite sources when summarizing the existing literature.
2. Using Specific Concepts or Data: Provide citations when discussing specific theories, models, or data.
3. Comparing Findings: Cite relevant studies when comparing or contrasting different findings.
4. Highlighting Research Gaps: Cite previous research when pointing out gaps your survey addresses.
5. Using Established Methods: Cite the creators of methodologies you employ in your survey.
6. Supporting Arguments: Cite sources that back up your conclusions and arguments.
7. Suggesting Future Research: Reference studies related to proposed future research directions.
---

Now you need to check whether the citations of "paper_title" in this subsection is correct.
A correct citation means that, the content of corresponding paper can support the sentences you write.
Once the citation can not support the sentence you write, correct the paper_title in '[]' or just remove it.

Remember that you can only cite the 'paper_title' provided above!!!
Any other informations like authors are not allowed cited!!!
Do not change any other things except the citations!!!
</instruction>
Only return the subsection with correct citations:
'''
