import os
import json
from datetime import datetime
from app.pipeline import run_end_to_end

INPUT_DIR = os.path.join("data", "inputs")
OUTPUT_DIR = os.path.join("data", "outputs")

def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([f for f in os.listdir(INPUT_DIR) if not f.startswith(".")])
    if not files:
        print(f"No input files found in {INPUT_DIR}. Drop PDFs/DOCX/IMG/TXT there and rerun.")
        return

    print(f"Found {len(files)} file(s) in {INPUT_DIR}.\n")

    for idx, fname in enumerate(files, start=1):
        file_path = os.path.join(INPUT_DIR, fname)
        print("\n" + "=" * 60)
        print(f"[{idx}/{len(files)}] Processing: {fname}")
        print("=" * 60)

        try:
            extracted, verified, plan = run_end_to_end(file_path)

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_json = os.path.join(
                OUTPUT_DIR,
                f"{os.path.splitext(extracted.file_name)[0]}_{stamp}_careplan.json"
            )

            payload = {
                "file_name": extracted.file_name,
                "file_type": extracted.file_type,
                "extraction_method": extracted.extraction_method,
                "warnings": extracted.warnings,
                "verified_text": verified.verified_text,
                "user_notes": verified.user_notes,
                "care_plan": plan.model_dump(),
            }

            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            print("Saved output to:", out_json)

        except Exception as e:
            print("ERROR processing", fname)
            print(e)

    print("\nDone. All files processed.")

if __name__ == "__main__":
    main()