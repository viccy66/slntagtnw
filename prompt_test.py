import json
import sys

from tools import analyze_intent


if len(sys.argv) < 2:
    print("Usage: python prompt_test.py \"votre question\"")
    raise SystemExit(1)

question = " ".join(sys.argv[1:])
raw = analyze_intent(question)

print("RAW OUTPUT:")
print(raw)

print("\nPARSED JSON:")
try:
    parsed = json.loads(raw)
    print(parsed)
    print("\nINTENTION:", parsed.get("intention"))
    print("VALEUR:", parsed.get("valeur"))
except Exception as exc:
    print(f"JSON invalide: {exc}")
