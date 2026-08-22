"""
shuffle_dataset.py
Memory-efficient dataset shuffle.
"""

import random
import tempfile
from pathlib import Path

CHUNK_SIZE = 100000

def shuffle_file(input_file, output_file):
    chunks = []
    with open(
        input_file,
        "r",
        encoding="utf8"
    ) as file:

        while True:
            lines = []
            for _ in range(CHUNK_SIZE):
                line = file.readline()

                if not line:
                    break
                lines.append(line)

            if not lines:
                break

            random.shuffle(lines)

            temp = tempfile.NamedTemporaryFile(
                delete=False,
                mode="w",
                encoding="utf8"
            )
            temp.writelines(lines)
            temp.close()
            chunks.append(temp.name)

    random.shuffle(chunks)

    with open(
        output_file,
        "w",
        encoding="utf8"
    ) as out:

        for chunk in chunks:
            with open(
                chunk,
                "r",
                encoding="utf8"
            ) as file:

                for line in file:

                    out.write(line)

            Path(chunk).unlink()