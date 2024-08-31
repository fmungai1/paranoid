#!/usr/bin/env python3

"""Main game script."""

import arcade

from paranoid.utilities import load_fonts
from paranoid.views import GameIntroView


class ParanoidGame(arcade.Window):
    """Main game window."""

    def __init__(self):
        """Initialize attributes."""
        super().__init__(fullscreen=True)

        # Initialize the game variables
        self.score = 0
        self.lives = 3
        self.level_number = 0
        self.display_score = 0

        self.show_view(GameIntroView(self))
        self.set_mouse_visible(False)

    def reset_game(self):
        """Reset the game variables."""
        self.score = 0
        self.lives = 3
        self.level_number = 0
        self.display_score = 0


def main():
    """Run the game."""
    ParanoidGame()
    arcade.run()


if __name__ == "__main__":
    load_fonts()
    main()
