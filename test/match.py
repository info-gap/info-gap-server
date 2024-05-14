import re

# Match for programming language
pattern = r"The name of the programming language is `(.+?)`"
response = "Yes! The name of the programming language is `LMQL` (short for Language Model Query Language). The language is designed for `prompting large language models and enabling easy adaptation to many tasks while abstracting language model internals and providing high-level semantics.`"
match = re.search(pattern, response)
language_name = ""
if match:
    language_name = match.group(1)
    print(language_name)
else:
    print(match)
