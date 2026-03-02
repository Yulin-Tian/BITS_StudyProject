from .schemas import ExtractedDoc, VerifiedDoc

def review_and_confirm(extracted: ExtractedDoc) -> VerifiedDoc:
    print("\n==============================")
    print(f"FILE: {extracted.file_name}")
    print(f"TYPE: {extracted.file_type} | METHOD: {extracted.extraction_method}")
    if extracted.warnings:
        print("WARNINGS:")
        for w in extracted.warnings:
            print(" -", w)

    print("\n----- EXTRACTED TEXT START -----\n")
    print(extracted.extracted_text[:8000])  # show first chunk
    if len(extracted.extracted_text) > 8000:
        print("\n... (truncated display) ...\n")
    print("\n----- EXTRACTED TEXT END -----\n")

    print("Human-in-the-loop check: paste corrected text below.")
    print("Tip: if it looks correct, just press Enter on the first line then type :wq on a new line.\n")

    lines = []
    first = input()
    if first.strip() == "":
        # user wants to keep original, require explicit :wq
        while True:
            line = input()
            if line.strip() == ":wq":
                break
        verified_text = extracted.extracted_text
    else:
        lines.append(first)
        while True:
            line = input()
            if line.strip() == ":wq":
                break
            lines.append(line)
        verified_text = "\n".join(lines).strip()

    notes = input("\nOptional notes (symptoms, constraints, etc). Or press Enter: ").strip() or None
    return VerifiedDoc(file_name=extracted.file_name, verified_text=verified_text, user_notes=notes)