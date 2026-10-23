"""python -m scenarios week [--healthy] [--out DIR] [--otlp] [--speed N] [--gzip]
python -m scenarios constructed [--out DIR]"""
import sys

USAGE = ("Usage: python -m scenarios week [--healthy] [--out DIR] [--otlp] [--speed N] [--gzip]\n"
         "       python -m scenarios constructed [--out DIR]")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("week", "constructed"):
        sys.exit(USAGE)
    if sys.argv[1] == "week":
        from .week import main
    else:
        from .constructed import main
    main(sys.argv[2:])
