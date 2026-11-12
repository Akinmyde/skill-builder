"""Export meeting notes to a Word file."""

import sys

import docx


def main(path):
    document = docx.Document()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            document.add_paragraph(line.rstrip())
    document.save(path.rsplit(".", 1)[0] + ".docx")


if __name__ == "__main__":
    main(sys.argv[1])
