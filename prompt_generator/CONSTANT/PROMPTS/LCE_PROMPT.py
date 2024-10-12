LCE_PROMPT = '''
You are an expert in artificial intelligence who wants to write a overall and comprehensive survey about [TOPIC].

Now you need to help to refine one of the subsection to improve th ecoherence of your survey.

You are provied with the content of the subsection along with the previous subsections and following subsections.

Previous Subsection:
--- 
[PREVIOUS]
---

Following Subsection:
---
[FOLLOWING]
---

Subsection to Refine: 
---
[SUBSECTION]
---


If the content of Previous Subsection is empty, it means that the subsection to refine is the first subsection.
If the content of Following Subsection is empty, it means that the subsection to refine is the last subsection.

Now refine the subsection to enhance coherence, and ensure that the content of the subsection flow more smoothly with the previous and following subsections. 

Remember that keep all the essence and core information of the subsection intact. Do not modify any citations in [] following the sentences.

Only return the whole refined content of the subsection without any other informations (like "Here is the refined subsection:")!

The subsection content:
'''
