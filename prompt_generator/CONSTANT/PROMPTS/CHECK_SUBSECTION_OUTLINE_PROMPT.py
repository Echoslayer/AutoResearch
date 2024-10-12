CHECK_SUBSECTION_OUTLINE_PROMPT = '''
You are an expert in artificial intelligence tasked with reviewing and improving subsection outlines.\n\
Current subsection outline:
---
[CURRENT SUBSECTION OUTLINE]
---
<DEFINITION>
1. Each subsection should have a clear and concise name.
2. Aim for consistency in the level of detail across all subsections.
3. Each subsection should have a brief description following its name.
4. List all subsections directly without using "..." to indicate additional ones.
5. Use the <format> and </format> tags only once to enclose the entire outline.
6. Ensure the </format> tag is included at the end of the outline.
7. Dont skip the words "Subsection" and "Description" between the <format> and </format> tag.
8. The number of "Subsection" and "Description" should be same. 
</DEFINITION>

Follow the DEFINITION and output with this format:
<format>
Subsection 1: [NAME OF SUBSECTION 1]
Description 1: [IMPROVED DESCRIPTION OF SUBSECTION 1]

Subsection 2: [NAME OF SUBSECTION 2]
Description 2: [IMPROVED DESCRIPTION OF SUBSECTION 2]

Subsection 3: [NAME OF SUBSECTION 3]
Description 3: [IMPROVED DESCRIPTION OF SUBSECTION 3]

[Continue with additional subsections as needed]
</format>
Only return the subsection outline without any other information.
'''
