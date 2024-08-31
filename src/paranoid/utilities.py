"""Helper functions."""

import os
import time
from collections import namedtuple

import pyglet.font

from paranoid.constants import (
    BGOTHL,
    BGOTHM,
    FONTS_BASE_PATH,
    HIGH_SCORES_FILE,
)


def load_fonts():
    """Load fonts from the font directory in they are not installed in the system."""
    pyglet.font.add_directory(FONTS_BASE_PATH)
    if pyglet.font.have_font(BGOTHL) and pyglet.font.have_font(BGOTHM):
        print("Yes! We have these fonts")


def create_high_scores():
    """Generate the default high-scores file."""
    with open(HIGH_SCORES_FILE, "w") as high_scores_file:
        high_scores_file.write("name,level,score,datetime\n")
        for i in range(10, 0, -1):
            if i % 2 == 0:  # even
                high_scores_file.write(f"Freddy,{int(i/2)},{i*5000},{time.asctime()}\n")
            else:
                high_scores_file.write(
                    f"BBB,{int((i+1)/2)},{i*5000},{time.asctime()}\n",
                )


def get_high_scores():
    """
    Get the 10 best scores from the high-scores file.

    :return: a list of namedtuples which represent each entry
    """
    Entry = namedtuple("Entry", "name level score")
    high_scores_list: list[Entry] = []

    # If HIGH_SCORES_FILE does not exist, create it TODO: Use sqlite db instead of flat file
    if not os.path.isfile(HIGH_SCORES_FILE):
        create_high_scores()

    with open(HIGH_SCORES_FILE) as high_scores_file:
        next(high_scores_file)  # Skip the heading
        for line in high_scores_file:
            # Ignore datetime column - only used to see how often game is played
            row = line.split(",")
            name, level, score = row[0], row[1], int(row[2])  # Save score as int
            high_scores_list.append(Entry(name, level, score))

    return sorted(high_scores_list, key=lambda entry: entry.score, reverse=True)[:10]
