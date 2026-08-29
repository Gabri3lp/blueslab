with open("tools/extract_data.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix the integer comparison on cid
code = code.replace("if cid and cid > 0:", "if cid and safe_int(cid) > 0:")
code = code.replace("child_passives.append({\n                                \"id\": cid,", "child_passives.append({\n                                \"id\": safe_int(cid),")

with open("tools/extract_data.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Patched tools/extract_data.py")