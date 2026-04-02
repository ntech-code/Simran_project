with open("api/routers/analytics.py", "r") as f:
    text = f.read()
text = text.replace("import pdfplumber", "import pdfplumber\n        print(f'DEBUG: UPLOADED FILES {list(file_contents.keys())}', flush=True)")
text = text.replace("agent = DocumentTaxParserAgent()", "print(f'DEBUG: EXTRACTED LENGTH = {len(combined_text)}', flush=True)\n        agent = DocumentTaxParserAgent()")
with open("api/routers/analytics.py", "w") as f:
    f.write(text)
