#!/usr/bin/env python3

"""
Project: Paranoid Game
Author: Fredrick Mungai https://github.com/fmungai1
Start date: 10th Aug 2020
"""

import arcade
import paranoid.levels as levels


class ParanoidGame(arcade.Window):
    def __init__(self):
        super().__init__(fullscreen=True)

        # Initialize the game variables
        self.score = 0
        self.lives = 3
        self.level_number = 0
        self.display_score = 0

        self.show_view(levels.GameIntroView(self))
        # self.show_view(levels.MainMenuView(self))
        self.set_mouse_visible(False)

    def reset_game(self):
        """
        Resets the game variables
        """
        self.score = 0
        self.lives = 3
        self.level_number = 0
        self.display_score = 0


def main():
    ParanoidGame()
    arcade.run()


if __name__ == '__main__':
    main()
