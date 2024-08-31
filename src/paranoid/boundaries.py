"""
The different types of boundaries and blocks used in the game.

Created using MS Paint app
Colors obtained using color picker on the original game
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Level" in DisplayInfoBlock `__init__` method
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade

from paranoid.constants import (
    AUDIO_BASE_PATH,
    BONUS_COLLECTED,
    BONUS_NOT_COLLECTED,
    BOUNDARY_THICKNESS,
    DEMO_TEXT,
    DISPLAY_BLOCK_NUMBERS,
    DISPLAY_BLOCK_TEXT,
    DISPLAY_BLOCK_TEXT_KEY,
    IMAGES_BASE_PATH,
    PAUSE_TIME,
    PLAYING_FIELD_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_PADDING,
    SCREEN_WIDTH,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Level


class Boundary(ABC):
    """Base class for boundaries."""

    def __init__(self):
        """Initialize boundary."""
        # Boundary constants
        self.center_x = SCREEN_PADDING + BOUNDARY_THICKNESS + PLAYING_FIELD_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2
        self.inner_left = SCREEN_PADDING + BOUNDARY_THICKNESS
        self.inner_right = self.inner_left + PLAYING_FIELD_WIDTH
        self.inner_bottom = self.inner_left
        self.inner_top = SCREEN_HEIGHT - self.inner_bottom

        self.is_fullscreen = False

        # Sounds
        self.top_hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/hit_top_boundary.wav",
        )
        self.side_hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/hit_side_boundary.wav",
        )
        self.bottom_hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/hit_bottom_boundary.wav",
        )

        self.border_list = arcade.SpriteList(is_static=True)
        self.populate_border_list()  # May override other attributes, hence is last in __init__

    @abstractmethod
    def populate_border_list(self):
        """Override to populate the border sprite list."""

    def draw(self):
        """Draw the boundary."""
        self.border_list.draw()


class PlayingFieldBoundary(Boundary):
    """The playing field boundary."""

    def populate_border_list(self):
        """Add the 4 borders for the playing field boundary."""
        # Each border is a sprite on its own so that the boundary can be drawn last
        # in a level. It has to be drawn last to hide balls, icons and bullets that
        # have passed it

        # Left and right borders
        for side in ["left", "right"]:
            border = arcade.Sprite(
                f"{IMAGES_BASE_PATH}/boundaries/playing_field_{side}_vertical_border.png",
                center_y=self.center_y,
            )
            if side == "left":
                border.right = self.inner_left
            else:
                border.left = self.inner_right
            self.border_list.append(border)

        # Top and bottom borders
        for i in range(2):
            border = arcade.Sprite(
                f"{IMAGES_BASE_PATH}/boundaries/playing_field_horizontal_border.png",
                center_x=self.center_x,
            )
            if i == 0:
                border.bottom = self.inner_top
            else:
                border.top = self.inner_bottom
            self.border_list.append(border)

        # Add a black rectangle at the top to hide the bullets due to larger size
        border = arcade.SpriteSolidColor(
            PLAYING_FIELD_WIDTH,
            SCREEN_PADDING * 2,
            arcade.color.BLACK,
        )
        border.center_x = self.center_x
        border.bottom = self.inner_top + BOUNDARY_THICKNESS
        self.border_list.append(border)


class FullscreenBoundary(Boundary):
    """The fullscreen boundary."""

    def populate_border_list(self):
        """Add the full screen boundary image."""
        # Override boundary constants
        self.center_x = SCREEN_WIDTH / 2
        self.inner_right = SCREEN_WIDTH - self.inner_left

        self.is_fullscreen = True

        # Drawn as one sprite for simplicity. Hence, it has to be drawn first in a View
        # because of black background. Converting background to transparent made it shrink
        self.border_list.append(
            arcade.Sprite(
                f"{IMAGES_BASE_PATH}/boundaries/fullscreen_boundary_black_background.png",
                center_x=self.center_x,
                center_y=self.center_y,
            ),
        )


class DisplayInfoBlock:
    """Normal-level display-info-block."""

    def __init__(self, level: Level):
        """
        Initialize the display block.

        :param level: used to access level attributes
        """
        self.level = level

        self.block_list = arcade.SpriteList(is_static=True)
        self.block = arcade.Sprite(
            f"{IMAGES_BASE_PATH}/boundaries/display_info_block_black_background.png",
            center_x=SCREEN_WIDTH - SCREEN_PADDING - 180,
            center_y=SCREEN_HEIGHT / 2,
        )
        self.block_list.append(self.block)

        self.start_x = SCREEN_WIDTH - 68
        self.start_y = SCREEN_HEIGHT - 134

        self.text_1 = ""
        self.text_2 = ""

    def draw(self):
        """Add additional text info."""
        self.block_list.draw()

        # Creates the addition effect of the score
        if self.level.window.display_score < self.level.window.score:
            self.level.window.display_score += 5

        # Draws text info on the display block
        arcade.draw_text(
            f"{self.level.window.display_score:,d}",
            self.start_x,
            self.start_y,
            **DISPLAY_BLOCK_NUMBERS,
        )
        arcade.draw_text(
            f"{self.level.window.level_number:,d}",
            self.start_x,
            self.start_y - 150,
            **DISPLAY_BLOCK_NUMBERS,
        )
        arcade.draw_text(
            f"{self.level.window.lives:,d}",
            self.start_x,
            self.start_y - 300,
            **DISPLAY_BLOCK_NUMBERS,
        )

        # Only draw bonus score at the end of the level, otherwise draw the bonus letters
        if self.level.level_complete and self.level.elapsed_time > PAUSE_TIME:
            arcade.draw_text(
                f"{self.level.bonus_score:,d}",
                self.start_x,
                self.start_y - 450,
                **DISPLAY_BLOCK_NUMBERS,
            )
        else:
            for index, letter in enumerate("BONUS"):
                if letter in self.level.bonus_collection_order:
                    style = BONUS_COLLECTED
                else:
                    style = BONUS_NOT_COLLECTED

                arcade.draw_text(
                    letter,
                    self.start_x - 220 + index * 50,
                    self.start_y - 430,
                    **style,
                )

        # Draws the playing instructions
        if not self.level.level_complete and not self.level.game_over:
            self.text_1 = "SPACE"

            if self.level.paddle.is_shooter_active:
                self.text_2 = "to shoot"
            elif self.level.paddle.is_magnetic:
                self.text_2 = "to release"
            elif not self.level.game_is_active:
                self.text_2 = "to start"
            else:
                self.text_1 = "ESC"
                self.text_2 = "to pause"
            arcade.draw_text("Press", self.block.center_x, 184, **DISPLAY_BLOCK_TEXT)
            arcade.draw_text(
                self.text_1,
                self.block.center_x,
                134,
                **DISPLAY_BLOCK_TEXT_KEY,
            )
            arcade.draw_text(self.text_2, self.block.center_x, 84, **DISPLAY_BLOCK_TEXT)


class DemoDisplayInfoBlock:
    """Demo-level display-info-block."""

    def __init__(self):
        """Initialize the display block."""
        self.block_list = arcade.SpriteList(is_static=True)
        self.block_list.append(
            arcade.Sprite(
                f"{IMAGES_BASE_PATH}/boundaries/demo_display_info_block.png",
                center_x=SCREEN_WIDTH - SCREEN_PADDING - 180,
                center_y=SCREEN_HEIGHT / 2,
            ),
        )

    def draw(self):
        """Draws the display block."""
        self.block_list.draw()
        arcade.draw_text(
            "Demo",
            PLAYING_FIELD_WIDTH / 2 + SCREEN_PADDING + BOUNDARY_THICKNESS,
            200,
            **DEMO_TEXT,
        )
