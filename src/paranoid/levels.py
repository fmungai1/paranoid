"""
Contains boundaries, levels and views used in the game
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "ParanoidGame" in Level __init__ method
from __future__ import annotations
from pathlib import Path

import arcade
import paranoid.assets as assets
import random
import time
import os

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union, Optional
from arcade.gui import UIInputBox, UIManager
from collections import namedtuple

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.main import ParanoidGame

# I programmed this specifically for the screen size I was working with
# at the time (1536 x 864 pixels) - fullscreen TODO: Add support for different screen sizes
SCREEN_WIDTH = 1536
SCREEN_HEIGHT = 864

# All the images drawn are based on these constants. Changing these constants will
# require redrawing all the images!!
SCREEN_PADDING = 10
BOUNDARY_THICKNESS = 25
PLAYING_FIELD_WIDTH = 1080  # Playing field height is calculated from screen height
BRICK_WIDTH = 75
BRICK_HEIGHT = 25
BRICK_MARGIN = 2
COLUMNS = 14  # Number of columns on the playing field

PAUSE_TIME = 3
TRANSITION_TIME = 1
DEMO_LEVEL_TIME = 12
RANDOM_BALLS = 10
NORMAL_VOLUME = 0.3
LOW_VOLUME = 0.1

# Bouncing constants
MAX_BOUNCES = 3
GRAVITY = 0.4
VELOCITY_RETAINED = 0.7

# Assets
ASSETS_BASE_PATH = Path(__file__).parent.parent.parent / "assets"
IMAGES_BASE_PATH = ASSETS_BASE_PATH / "images"
AUDIO_BASE_PATH = ASSETS_BASE_PATH / "audio"
FONTS_BASE_PATH = ASSETS_BASE_PATH / "fonts"
HIGH_SCORES_FILE = ASSETS_BASE_PATH / "high_scores.txt"

# Global Sounds
ENTER_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/press_enter.wav")
SCROLL_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/scroll_options.wav")
WHOOSH_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/whoosh_1.wav")

# Fonts: path to font .ttf files
BGOTHL = f"{FONTS_BASE_PATH}/bgothl"  # BankGothic Lt BT
BGOTHM = f"{FONTS_BASE_PATH}/bgothm"  # BankGothic Md BT

# Text-styling dictionaries
DISPLAY_BLOCK_NUMBERS = {"color": (85, 255, 255),
                         "font_size": 30,
                         "font_name": BGOTHL,
                         "anchor_x": "right"}

DISPLAY_BLOCK_TEXT = {"color": (0, 0, 170),
                      "font_size": 30,
                      "font_name": BGOTHL,
                      "width": 280,
                      "align": "center",
                      "anchor_x": "center",
                      "anchor_y": "center"}

DEMO_TEXT = {"color": (150, 150, 150),
             "font_size": 80,
             "font_name": BGOTHM,
             "anchor_x": "center",
             "anchor_y": "center"}

DISPLAY_BLOCK_TEXT_KEY = DISPLAY_BLOCK_TEXT.copy()
DISPLAY_BLOCK_TEXT_KEY.update(color=(170, 0, 0))

BONUS_NOT_COLLECTED = {"color": (170, 170, 170),
                       "font_size": 30,
                       "font_name": BGOTHL,
                       "anchor_x": "center",
                       "anchor_y": "center"}

BONUS_COLLECTED = {"color": (85, 255, 85),
                   "font_size": 35,
                   "font_name": BGOTHM,
                   "anchor_x": "center",
                   "anchor_y": "center"}

LEVEL_INFO_TEXT = {"color": (215, 215, 215),
                   "font_size": 40,
                   "font_name": BGOTHM,
                   "anchor_x": "center",
                   "anchor_y": "center"}

MENU_TEXT_HEADING = {"color": (255, 85, 85),
                     "font_size": 65,
                     "font_name": BGOTHM,
                     "anchor_x": "center",
                     "anchor_y": "center"}

MENU_TEXT_NORMAL = {"color": (215, 215, 215),
                    "font_size": 40,
                    "font_name": BGOTHL,
                    "anchor_x": "center",
                    "anchor_y": "center"}

MENU_TEXT_SELECTED = {"color": (85, 255, 255),
                      "font_size": 50,
                      "font_name": BGOTHM,
                      "anchor_x": "center",
                      "anchor_y": "center"}

ENTER_NAME_HEADING = MENU_TEXT_HEADING.copy()
ENTER_NAME_HEADING.update(font_size=50)

CONFIRMATION_DIALOGUE_TEXT = {"color": (215, 215, 215),
                              "font_size": 30,
                              "font_name": BGOTHL,
                              "anchor_x": "center",
                              "anchor_y": "center"}

LEADER_BOARD_HEADING = {"color": (170, 0, 0),
                        "font_size": 100,
                        "font_name": BGOTHM,
                        "anchor_x": "center",
                        "anchor_y": "center"}

HIGH_SCORES_HEADING = {"color": (0, 0, 170),
                       "font_size": 30,
                       "font_name": BGOTHM,
                       "anchor_x": "center",
                       "anchor_y": "center"}

HIGH_SCORES_NUMBERS = {"color": arcade.color.BLACK,
                       "font_size": 20,
                       "font_name": BGOTHL,
                       "anchor_x": "right",
                       "anchor_y": "center"}

HIGH_SCORES_NAMES = {"color": arcade.color.BLACK,
                     "font_size": 20,
                     "font_name": BGOTHL,
                     "anchor_x": "left",
                     "anchor_y": "center"}

HOW_TO_PLAY_TEXT = {"color": (85, 255, 85),
                    "font_size": 30,
                    "font_name": BGOTHL,
                    "anchor_x": "center",
                    "anchor_y": "center"}

HOW_TO_PLAY_NEXT_BACK = MENU_TEXT_HEADING.copy()
HOW_TO_PLAY_NEXT_BACK.update(font_size=50)


def create_high_scores():
    """
    Generates the default high scores file
    """
    with open(HIGH_SCORES_FILE, "w") as high_scores_file:
        high_scores_file.write("name,level,score,datetime\n")
        for i in range(10, 0, -1):
            if i % 2 == 0:  # even
                high_scores_file.write(f"Freddy,{int(i/2)},{i*5000},{time.asctime()}\n")
            else:
                high_scores_file.write(f"BBB,{int((i+1)/2)},{i*5000},{time.asctime()}\n")


def get_high_scores():
    """
    Gets the 10 best scores from the high_scores file

    :return: a list of namedtuples which represent each entry
    """
    Entry = namedtuple("Entry", "name level score")
    high_scores_list = []

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


HIGH_SCORES = get_high_scores()


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                   BOUNDARIES AND DISPLAY BLOCKS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Boundary(ABC):
    """
    Base class for boundaries
    """

    def __init__(self):
        # Boundary constants
        self.center_x = SCREEN_PADDING + BOUNDARY_THICKNESS + PLAYING_FIELD_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2
        self.inner_left = SCREEN_PADDING + BOUNDARY_THICKNESS
        self.inner_right = self.inner_left + PLAYING_FIELD_WIDTH
        self.inner_bottom = self.inner_left
        self.inner_top = SCREEN_HEIGHT - self.inner_bottom

        self.is_fullscreen = False

        # Sounds
        self.top_hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_top_boundary.wav")
        self.side_hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_side_boundary.wav")
        self.bottom_hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_bottom_boundary.wav")

        self.border_list = arcade.SpriteList(is_static=True)
        self.populate_border_list()  # May override other attributes, hence is last in __init__

    @abstractmethod
    def populate_border_list(self):
        """
        Override to populate the border sprite list
        """
        pass

    def draw(self):
        self.border_list.draw()


class PlayingFieldBoundary(Boundary):
    """
    Creates the playing field boundary
    """

    def populate_border_list(self):
        # Each border is a sprite on its own so that the boundary can be drawn last
        # in a level. It has to be drawn last to hide balls, icons and bullets that
        # have passed it

        # Left and right borders
        for side in ["left", "right"]:
            border = arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/playing_field_{side}_vertical_border.png",
                                   center_y=self.center_y)
            if side == "left":
                border.right = self.inner_left
            else:
                border.left = self.inner_right
            self.border_list.append(border)

        # Top and bottom borders
        for i in range(2):
            border = arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/playing_field_horizontal_border.png",
                                   center_x=self.center_x)
            if i == 0:
                border.bottom = self.inner_top
            else:
                border.top = self.inner_bottom
            self.border_list.append(border)

        # Add a black rectangle at the top to hide the bullets due to larger size
        border = arcade.SpriteSolidColor(PLAYING_FIELD_WIDTH, SCREEN_PADDING * 2, arcade.color.BLACK)
        border.center_x = self.center_x
        border.bottom = self.inner_top + BOUNDARY_THICKNESS
        self.border_list.append(border)


class FullscreenBoundary(Boundary):
    """
    Creates the fullscreen boundary
    """

    def populate_border_list(self):
        # Override boundary constants
        self.center_x = SCREEN_WIDTH / 2
        self.inner_right = SCREEN_WIDTH - self.inner_left

        self.is_fullscreen = True

        # Drawn as one sprite for simplicity. Hence, it has to be drawn first in a View
        # because of black background. Converting background to transparent made it shrink
        self.border_list.append(arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/fullscreen_boundary_black_background.png",
                                              center_x=self.center_x, center_y=self.center_y))


class DisplayInfoBlock:
    """
    Creates the normal-level display-info-block
    """

    def __init__(self, level: Level):
        """
        Initializes the display block

        :param level: used to access level attributes
        """
        self.level = level

        self.block_list = arcade.SpriteList(is_static=True)
        self.block = arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/display_info_block_black_background.png",
                                   center_x=SCREEN_WIDTH - SCREEN_PADDING - 180,
                                   center_y=SCREEN_HEIGHT / 2)
        self.block_list.append(self.block)

        self.start_x = SCREEN_WIDTH - 68
        self.start_y = SCREEN_HEIGHT - 134

        self.text_1 = ""
        self.text_2 = ""

    def draw(self):
        """
        Adds additional text info
        """
        self.block_list.draw()

        # Creates the addition effect of the score
        if self.level.window.display_score < self.level.window.score:
            self.level.window.display_score += 5

        # Draws text info on the display block
        arcade.draw_text(f"{self.level.window.display_score:,d}", self.start_x, self.start_y,
                         **DISPLAY_BLOCK_NUMBERS)
        arcade.draw_text(f"{self.level.window.level_number:,d}", self.start_x, self.start_y - 150,
                         **DISPLAY_BLOCK_NUMBERS)
        arcade.draw_text(f"{self.level.window.lives:,d}", self.start_x, self.start_y - 300,
                         **DISPLAY_BLOCK_NUMBERS)

        # Only draw bonus score at the end of the level, otherwise draw the bonus letters
        if self.level.level_complete and self.level.elapsed_time > PAUSE_TIME:
            arcade.draw_text(f"{self.level.bonus_score:,d}", self.start_x, self.start_y - 450,
                             **DISPLAY_BLOCK_NUMBERS)
        else:
            for index, letter in enumerate("BONUS"):
                if letter in self.level.bonus_collection_order:
                    style = BONUS_COLLECTED
                else:
                    style = BONUS_NOT_COLLECTED

                arcade.draw_text(letter, self.start_x - 220 + index * 50, self.start_y - 430,
                                 **style)

        # Draws the playing instructions
        if not self.level.level_complete and not self.level.game_over:
            self.text_1 = "SPACE"

            if self.level.paddle.activate_shooter:
                self.text_2 = "to shoot"
            elif self.level.paddle.is_magnetic:
                self.text_2 = "to release"
            elif not self.level.game_is_active:
                self.text_2 = "to start"
            else:
                self.text_1 = "ESC"
                self.text_2 = "to pause"
            arcade.draw_text("Press", self.block.center_x, 184, **DISPLAY_BLOCK_TEXT)
            arcade.draw_text(self.text_1, self.block.center_x, 134, **DISPLAY_BLOCK_TEXT_KEY)
            arcade.draw_text(self.text_2, self.block.center_x, 84, **DISPLAY_BLOCK_TEXT)


class DemoDisplayInfoBlock:
    """
    Creates the demo-level display-info-block
    """
    def __init__(self):
        """
        Initializes the display block
        """
        self.block_list = arcade.SpriteList(is_static=True)
        self.block_list.append(arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/demo_display_info_block.png",
                                             center_x=SCREEN_WIDTH - SCREEN_PADDING - 180,
                                             center_y=SCREEN_HEIGHT / 2))

    def draw(self):
        """
        Draws the display block
        """
        self.block_list.draw()
        arcade.draw_text("Demo", PLAYING_FIELD_WIDTH / 2 + SCREEN_PADDING + BOUNDARY_THICKNESS,
                         200, **DEMO_TEXT)


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             LEVELS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Shortened names for brick classes to be used in populating the grid (4 chars per brick)
RED_ = assets.RedBrick
BLUE = assets.BlueBrick
GRN_ = assets.GreenBrick
AQUA = assets.AquaBrick
GREY = assets.GreyBrick
REDL = assets.RedLineBrick
BLUL = assets.BlueLineBrick
GRNL = assets.GreenLineBrick
AQUL = assets.AquaLineBrick
GRYL = assets.GreyLineBrick
PINK = assets.PinkBrick2
PNK1 = assets.PinkBrick1
REDB = assets.RedBlueBrick2
RDB1 = assets.RedBlueBrick1
MUL4 = assets.MultiColouredBrick4
MUL3 = assets.MultiColouredBrick3
MUL2 = assets.MultiColouredBrick2
MUL1 = assets.MultiColouredBrick1
UK__ = assets.UKFlagBrick
KNYA = assets.KenyanFlagBrick
CUP_ = assets.CupBrick
BBB_ = assets.BBBBrick
FNM_ = assets.FNMBrick
HAPY = assets.SmilingBrick
SAD_ = assets.FrowningBrick
LGRY = assets.LeftPointingGreyBrick
RGRY = assets.RightPointingGreyBrick
NWAL = assets.NormalWallBrick
RWAL = assets.RightWallBrick
BLOK = assets.UnbreakableBrick
BONB = assets.BonusBBrick
BONO = assets.BonusOBrick
BONN = assets.BonusNBrick
BONU = assets.BonusUBrick
BONS = assets.BonusSBrick

# Shortened names for icon classes to be used in populating the icons list
LENGTHEN = assets.LengthenPaddleIcon
SHORTEN = assets.ShortenPaddleIcon
MAGNET = assets.MagneticPaddleIcon
SCORE = assets.BonusScoreIcon
SHOOT = assets.ShootingIcon
SPLIT = assets.SplitBallIcon
LIFE = assets.BonusLifeIcon
SAFETY = assets.SafetyBarrierIcon
ADVANCE = assets.AdvanceLevelIcon
SPEED = assets.SpeedUpBallsIcon
SLOW = assets.SlowDownBallsIcon
INVINCIBLE = assets.InvinciBallIcon


class Level(arcade.View, ABC):
    """
    Base class for all levels
    """

    def __init__(self, window: ParanoidGame, is_demo_level=False):
        super().__init__()
        self.window = window
        self.is_demo_level = is_demo_level

        # Sprite lists
        self.brick_list = arcade.SpriteList(use_spatial_hash=True)  # Setting is_static causes bugs in multi-bricks
        self.breakable_brick_list = arcade.SpriteList()  # Only used to check if level is complete
        self.ball_list = arcade.SpriteList()
        self.icon_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Sprites and textures
        self.boundary = PlayingFieldBoundary()
        self.display_info = DisplayInfoBlock(level=self)
        self.level_info_boundary = arcade.load_texture(f"{IMAGES_BASE_PATH}/boundaries/level_info_boundary.png")
        self.paddle = assets.NormalPaddle(level=self)
        self.ball_list.append(assets.NormalBall(self.boundary, self.brick_list, level=self))

        # Level attributes
        self.first_time_showing = True
        self.game_over = False
        self.level_complete = False
        self.game_is_active = False
        self.lost_a_life = False
        self.bonus_added = False
        self.load_next_level = False
        self.game_over_voice_played = False
        self.left_pressed = False
        self.right_pressed = False

        # Variables
        self.bonus_score = 0
        self.bonus_collection_order = ""
        self.elapsed_time = 0
        self.elapsed_time_copy = 0
        self.window.level_number += 1

        # Sounds
        self.lost_a_life_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/lose_life.wav")
        self.game_over_voice = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/game_over_voice.wav")
        self.level_complete_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/level_complete_sound.wav")
        self.level_complete_voice = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/level_complete_voice.wav")
        self.adding_bonus_sound_1 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/adding_bonus_1.wav")
        self.adding_bonus_sound_2 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/adding_bonus_2.wav")
        self.adding_bonus_sound_3 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/adding_bonus_3.wav")
        self.shoot_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/shoot_bullet_sound.wav")
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/level_{self.window.level_number}"
                                             f"_music.mp3", streaming=True)

        # Overwrite certain attributes if we are in a demo level
        if self.is_demo_level:
            self.display_info = DemoDisplayInfoBlock()
            self.paddle = assets.DemoNormalPaddle(self)
            self.game_is_active = True

        # Level setup stuff
        self.grid = []
        self.icons = []
        self.populate_grid_and_icons()
        self.initialize_bricks_and_icons()

    @abstractmethod
    def populate_grid_and_icons(self):
        """
        Override to populate the grid with bricks in the desired positions. This is
        how the bricks will appear in each level. Also populate the list of icons
        that will appear in the level.

        self.grid = ...
        self.icons = ...
        """
        pass

    def initialize_bricks_and_icons(self):
        """
        Positions the bricks on the correct x, y coordinates based on the grid.
        Also adds icons randomly to some of the bricks
        """
        # Each row is a list of brick classes that can be called to instantiate the brick
        for row_number, row in enumerate(self.grid):
            for column_number, BrickType in enumerate(row):

                # None refers to an empty cell
                if BrickType is not None:

                    # Positioning starts at top left of playing field
                    # Horizontal positioning is done using .left attribute below
                    # center_x = self.boundary.inner_left + BRICK_MARGIN + BRICK_WIDTH / 2 + \
                    #            (BRICK_MARGIN + BRICK_WIDTH) * column_number

                    center_y = self.boundary.inner_top - BRICK_MARGIN - BRICK_HEIGHT / 2 - \
                               (BRICK_MARGIN + BRICK_HEIGHT) * row_number

                    brick = BrickType(center_y=center_y, level=self)

                    # Switched to positioning using left of the brick in order to create seamless
                    # images with wall bricks
                    brick.left = self.boundary.inner_left + BRICK_MARGIN + (BRICK_MARGIN + BRICK_WIDTH) \
                                 * column_number

                    # Will be used to check if level is complete
                    if brick.is_breakable:
                        self.breakable_brick_list.append(brick)

                    self.brick_list.append(brick)

        random_bricks = random.sample(list(self.breakable_brick_list), k=len(self.icons))

        # Random icon assignment to the bricks
        for brick, IconType in zip(random_bricks, self.icons):
            brick.icon = IconType(level=self)
            brick.icon.position = brick.position

    def level_is_complete(self):
        """
        Actions to execute when a level is complete
        """
        self.game_is_active = False
        self.level_complete = True
        self.elapsed_time = 0  # Reset the elapsed time
        self.background_music.stop()

        # Set the bonus score
        if len(self.bonus_collection_order) == 5:  # All bonus letters collected
            if self.bonus_collection_order == "BONUS":
                self.bonus_score = 5000
            else:
                self.bonus_score = 2000

        self.bonus_score += self.window.lives * 100
        self.level_complete_sound.play(volume=NORMAL_VOLUME)

    def lose_a_life(self):
        """
        Reduces the lives by one and checks whether the game is over
        """
        self.game_is_active = False
        self.window.lives -= 1

        if self.window.lives == 0:
            self.game_over = True
        else:
            self.lost_a_life = True

        self.elapsed_time = 0  # Reset the elapsed time
        self.background_music.stop()
        self.lost_a_life_sound.play(volume=NORMAL_VOLUME)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

        # For demo level, don't bounce
        if self.is_demo_level:
            self.background_music.play(volume=LOW_VOLUME)

        # For normal level, bounce when showing the first time
        else:
            if self.first_time_showing:
                self.first_time_showing = False
                self.window.show_view(BouncingIntroView(self))
            else:
                self.background_music.play(volume=LOW_VOLUME)

    def on_hide_view(self):
        self.background_music.stop()

    def on_update(self, delta_time: float):
        """
        Movement and game logic
        """
        self.elapsed_time += delta_time

        # If we are in a demo level, display for some time then return to main menu
        if self.is_demo_level and self.elapsed_time > DEMO_LEVEL_TIME:
            self.window.show_view(MainMenuView(self.window))
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

        # Loop the background music
        if self.background_music.get_stream_position() == 0:
            # Background music stops if level is complete, lost a life or game over.
            # This prevents immediate restart of the background music.
            # Also prevents restart of music when exiting demo level.
            if not self.lost_a_life and not self.game_over and not self.level_complete and \
                    not self.is_demo_level:
                self.background_music.play(volume=LOW_VOLUME)

        # Only update if the game is in active mode
        if self.game_is_active:
            self.ball_list.on_update()  # MUST update before paddle, see MagnetNormalBall
            self.paddle.on_update()
            self.icon_list.on_update()
            self.bullet_list.on_update()
            self.brick_list.update()

            # If all breakable bricks are broken, level is complete
            if not self.breakable_brick_list:
                self.level_is_complete()

            # If there is only one ball in the playing field and it goes down, lose a life
            elif not self.ball_list:
                self.lose_a_life()

        # Pause for a while before resetting the game
        # This method of pausing is better than using arcade.pause or time.sleep because it
        # allows execution to continue, i.e drawing and updating
        elif self.lost_a_life and self.elapsed_time > PAUSE_TIME + TRANSITION_TIME:
            self.paddle = assets.NormalPaddle(self)
            ball = assets.NormalBall(self.boundary, self.brick_list, self)
            self.ball_list.append(ball)

            self.background_music.play(volume=LOW_VOLUME)
            self.lost_a_life = False

        # Pause for a while before switching to the next view
        elif self.game_over and self.elapsed_time > PAUSE_TIME * 2 + TRANSITION_TIME and \
                self.window.display_score == self.window.score:
            # Check if we can get into the high scores list
            if self.window.score > HIGH_SCORES[-1].score:
                self.window.show_view(NameEntryView(self.window))
            else:
                self.window.show_view(HighScoreView(self.window))

            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

        # After the bonus score has been added, wait for the score to finish updating
        # then set load_next_level to True which allows next level to be initiated
        # (Checking if elapsed time > pause time + transition time eliminates a situation
        # where display score and score could be equal, yet bonus score has not been added
        # in on_draw method)
        elif self.level_complete and self.elapsed_time > PAUSE_TIME + TRANSITION_TIME and \
                self.window.display_score == self.window.score and not self.load_next_level:
            self.load_next_level = True
            self.elapsed_time_copy = self.elapsed_time  # Saves the current time

        # After the score has finished updating, wait for a while before
        # exiting the level
        elif self.load_next_level and self.elapsed_time > self.elapsed_time_copy + PAUSE_TIME - 1:
            self.window.show_view(LevelOutroView(self))

    def on_draw(self):
        arcade.start_render()

        self.display_info.draw()
        self.brick_list.draw()
        self.paddle.draw()
        self.ball_list.draw()
        self.icon_list.draw()
        self.bullet_list.draw()
        self.boundary.draw()  # Has to be drawn last to hide balls, icons and bullets

        # Pause for a while before displaying the game over message
        if self.game_over and self.elapsed_time > PAUSE_TIME + TRANSITION_TIME:
            arcade.draw_scaled_texture_rectangle(self.boundary.center_x, self.boundary.center_y,
                                                 self.level_info_boundary)
            arcade.draw_text("Game Over", self.boundary.center_x, self.boundary.center_y,
                             **LEVEL_INFO_TEXT)

            # Only play game over voice once
            if not self.game_over_voice_played:
                self.game_over_voice.play(volume=NORMAL_VOLUME)
                self.game_over_voice_played = True

        # Pause for a while before displaying the level complete message and adding bonus
        elif self.level_complete and self.elapsed_time > PAUSE_TIME:
            arcade.draw_scaled_texture_rectangle(self.boundary.center_x, self.boundary.center_y,
                                                 self.level_info_boundary)
            arcade.draw_text("Level", self.boundary.center_x, self.boundary.center_y + 30,
                             **LEVEL_INFO_TEXT)
            arcade.draw_text("Complete", self.boundary.center_x, self.boundary.center_y - 30,
                             **LEVEL_INFO_TEXT)

            # Add the bonus score only once
            if not self.bonus_added:
                self.window.score += self.bonus_score
                self.level_complete_voice.play(volume=NORMAL_VOLUME)

                # Play the adding_bonus_sound
                if self.bonus_score <= 1500:
                    self.adding_bonus_sound_1.play(volume=NORMAL_VOLUME)
                elif self.bonus_score <= 3500:
                    self.adding_bonus_sound_2.play(volume=NORMAL_VOLUME)
                else:
                    self.adding_bonus_sound_3.play(volume=NORMAL_VOLUME)

                self.bonus_added = True

    def on_key_press(self, symbol: int, modifiers: int):
        # If we are in a demo level, return to main menu
        if self.is_demo_level:
            self.window.show_view(MainMenuView(self.window))
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

        # Normal game play
        else:
            # Left
            if symbol == arcade.key.LEFT:
                self.left_pressed = True

            # Right
            elif symbol == arcade.key.RIGHT:
                self.right_pressed = True

            # Space
            elif symbol == arcade.key.SPACE:
                if not self.lost_a_life and not self.game_over and not self.level_complete:
                    self.game_is_active = True
                    if self.paddle.is_magnetic:
                        self.paddle.release_magnetic_balls()
                    if self.paddle.activate_shooter:
                        self.bullet_list.append(assets.Bullet(self))
                        self.shoot_sound.play(volume=NORMAL_VOLUME)

            # Escape
            elif symbol == arcade.key.ESCAPE:
                if not self.game_over and not self.level_complete:
                    self.window.show_view(PauseMenuView(self))
                    WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

                    # Prevent paddle from moving after un-pausing if left or right key was pressed
                    self.left_pressed = False
                    self.right_pressed = False

    def on_key_release(self, _symbol: int, _modifiers: int):
        if not self.is_demo_level:
            if _symbol == arcade.key.LEFT:
                self.left_pressed = False
            elif _symbol == arcade.key.RIGHT:
                self.right_pressed = False


class Level1(Level):
    def populate_grid_and_icons(self):
        # Although it may be easier to use loops and list comprehensions, I decided to create
        # each grid manually for easier visualization of the levels

        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, KNYA, UK__, None, None, None, None, None, None],
                     [None, None, None, None, None, None, UK__, KNYA, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_],
                     [BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
                     [GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_],
                     [AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, PINK, PINK, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA]]

        self.icons = [MAGNET, SHORTEN, SAFETY, LENGTHEN, SPEED]
        # self.icons += [SCORE, SHOOT, SPLIT, LIFE, ADVANCE, SLOW, INVINCIBLE]  # All icons


class Level2(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, None],
                     [None, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, None],
                     [None, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, GRN_, None],
                     [None, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, AQUL, None],
                     [None, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, None],
                     [None, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, None],
                     [None, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, None]]

        self.icons = [SPEED, SPLIT, SPLIT, SHOOT, SLOW, SCORE, LIFE]


class Level3(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL],
                     [None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL],
                     [SAD_, None, SAD_, None, SAD_, None, SAD_, None, SAD_, None, SAD_, None, SAD_, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL],
                     [None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY, None, HAPY],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, PINK, PINK, None, None, None, None, None, None]]

        self.icons = [SHOOT, LIFE, INVINCIBLE, SCORE, LENGTHEN]


class Level4(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
                     [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None]]

        self.icons = [SAFETY, SHORTEN, MAGNET, SPLIT, LENGTHEN, SHOOT, SCORE]


class Level5(Level):
    def populate_grid_and_icons(self):
        self.grid = [[BLUE, BLUE, BLUE, BLUE, BLUE, None, None, None, None, BLUE, BLUE, BLUE, BLUE, BLUE],
                     [BLUE, RED_, RED_, RED_, None, None, None, None, None, None, RED_, RED_, RED_, BLUE],
                     [BLUE, GRN_, GRN_, None, None, None, None, None, None, None, None, GRN_, GRN_, BLUE],
                     [BLUE, RED_, None, None, None, None, None, None, None, None, None, None, RED_, BLUE],
                     [BLUE, None, None, None, None, None, MUL4, None, None, None, None, None, None, BLUE],
                     [None, None, None, None, None, None, None, MUL4, None, None, None, None, None, None],
                     [BLUE, None, None, None, None, None, None, None, None, None, None, None, None, BLUE],
                     [BLUE, RED_, None, None, None, None, None, None, None, None, None, None, RED_, BLUE],
                     [BLUE, GRN_, GRN_, None, None, None, None, None, None, None, None, GRN_, GRN_, BLUE],
                     [BLUE, RED_, RED_, RED_, None, None, None, None, None, None, RED_, RED_, RED_, BLUE],
                     [BLUE, BLUE, BLUE, BLUE, BLUE, None, None, None, None, BLUE, BLUE, BLUE, BLUE, BLUE]]

        self.icons = [MAGNET, SCORE, MAGNET, SCORE, SHOOT, LIFE]


class Level6(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, REDL, None, None, None, None, None, None, BLUL, None, None, None],
                     [None, None, REDL, RGRY, REDL, None, None, None, None, BLUL, LGRY, BLUL, None, None],
                     [None, REDL, None, MUL4, None, REDL, None, None, BLUL, None, MUL4, None, BLUL, None],
                     [None, None, REDL, None, REDL, None, None, None, None, BLUL, None, BLUL, None, None],
                     [None, None, None, REDL, None, None, BLUL, REDL, None, None, BLUL, None, None, None],
                     [None, None, None, None, None, BLUL, BBB_, CUP_, REDL, None, None, None, None, None],
                     [None, None, None, None, None, REDL, CUP_, FNM_, BLUL, None, None, None, None, None],
                     [None, None, None, BLUL, None, None, REDL, BLUL, None, None, REDL, None, None, None],
                     [None, None, BLUL, None, BLUL, None, None, None, None, REDL, None, REDL, None, None],
                     [None, BLUL, None, MUL4, None, BLUL, None, None, REDL, None, MUL4, None, REDL, None],
                     [None, None, BLUL, RGRY, BLUL, None, None, None, None, REDL, LGRY, REDL, None, None],
                     [None, None, None, BLUL, None, None, None, None, None, None, REDL, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None],
                     [None, None, None, None, None, HAPY, None, None, HAPY, None, None, None, None, None],
                     [None, None, None, None, HAPY, None, PINK, PINK, None, HAPY, None, None, None, None],
                     [None, None, None, None, None, HAPY, None, None, HAPY, None, None, None, None, None],
                     [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None]]

        self.icons = [SCORE, LIFE, SAFETY, SCORE, LENGTHEN]


class Level7(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, None, None, None],
                     [None, None, None, GREY, BLUL, BLUL, BLUL, GRNL, GRNL, GRNL, GREY, None, None, None],
                     [None, None, None, GREY, BLUL, GREY, GREY, GREY, GREY, GRNL, GREY, None, None, None],
                     [None, None, None, GREY, BLUL, GREY, None, None, GREY, GRNL, GREY, None, None, None],
                     [None, None, None, GREY, GRNL, GREY, None, None, GREY, BLUL, GREY, None, None, None],
                     [None, None, None, GREY, GRNL, GREY, GREY, GREY, GREY, BLUL, GREY, None, None, None],
                     [None, None, None, GREY, GRNL, GRNL, GRNL, BLUL, BLUL, BLUL, GREY, None, None, None],
                     [None, None, None, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, None],
                     [None, GREY, GRNL, GRNL, GRNL, GRNL, GRNL, BLUL, BLUL, BLUL, BLUL, BLUL, GREY, None],
                     [None, GREY, GRNL, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, BLUL, GREY, None],
                     [None, GREY, GRNL, GREY, None, None, None, None, None, None, GREY, BLUL, GREY, None],
                     [None, GREY, BLUL, GREY, None, None, None, None, None, None, GREY, GRNL, GREY, None],
                     [None, GREY, BLUL, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GRNL, GREY, None],
                     [None, GREY, BLUL, BLUL, BLUL, BLUL, BLUL, GRNL, GRNL, GRNL, GRNL, GRNL, GREY, None],
                     [None, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, None]]

        self.icons = [SPEED, MAGNET, ADVANCE, SLOW, INVINCIBLE, SPLIT]


class Level8(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, MUL2, MUL2, None, None, None, None, None, None],
                     [None, None, None, None, None, None, REDB, REDB, None, None, None, None, None, None],
                     [RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [GREY, GRN_, GREY, GRN_, GREY, GRN_, GREY, GREY, GRN_, GREY, GRN_, GREY, GRN_, GREY],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, RGRY, RGRY, None, None, None, None, None, None, LGRY, LGRY, None, None],
                     [None, None, RGRY, RGRY, None, None, None, None, None, None, LGRY, LGRY, None, None]]

        self.icons = [SAFETY, SHORTEN, SPLIT, LENGTHEN, LIFE, SPEED, SPLIT, SHORTEN, SCORE]


class Level9(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, AQUA, AQUA, None, None, None, None, None, None, AQUA, AQUA, None, None],
                     [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
                     [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
                     [None, None, GREY, RED_, RED_, AQUA, None, None, AQUA, RED_, RED_, GREY, None, None],
                     [None, None, None, GREY, RED_, RED_, AQUA, AQUA, RED_, RED_, GREY, None, None, None],
                     [None, None, None, None, GREY, RED_, RED_, RED_, RED_, GREY, None, None, None, None],
                     [None, None, None, None, None, GREY, RED_, RED_, GREY, None, None, None, None, None],
                     [None, None, None, None, None, None, REDB, REDB, None, None, None, None, None, None],
                     [None, None, None, None, None, None, REDB, REDB, None, None, None, None, None, None],
                     [None, None, None, None, None, None, REDB, REDB, None, None, None, None, None, None],
                     [None, None, None, None, None, GREY, RED_, RED_, GREY, None, None, None, None, None],
                     [None, None, None, None, GREY, RED_, RED_, RED_, RED_, GREY, None, None, None, None],
                     [None, None, None, GREY, RED_, RED_, AQUA, AQUA, RED_, RED_, GREY, None, None, None],
                     [None, None, GREY, RED_, RED_, AQUA, None, None, AQUA, RED_, RED_, GREY, None, None],
                     [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
                     [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
                     [None, None, AQUA, AQUA, None, None, None, None, None, None, AQUA, AQUA, None, None]]

        self.icons = [LIFE, LENGTHEN, SHOOT, SPLIT, SPEED, SAFETY, SHOOT, LENGTHEN, SCORE, SLOW]


class Level10(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None],
                     [None, None, None, None, None, HAPY, None, None, HAPY, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
                     [None, RED_, None, RED_, None, RED_, None, None, RED_, None, RED_, None, RED_, None],
                     [None, None, None, None, None, None, PINK, UK__, None, None, None, None, None, None],
                     [None, None, None, None, None, None, KNYA, PINK, None, None, None, None, None, None],
                     [BLUE, None, BLUE, None, BLUE, None, BLUE, BLUE, None, BLUE, None, BLUE, None, BLUE],
                     [RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, SAD_, None, None, SAD_, None, None, None, None, None],
                     [None, None, None, None, None, None, SAD_, SAD_, None, None, None, None, None, None]]

        self.icons = [INVINCIBLE, LENGTHEN, SCORE, SAFETY, SHORTEN, SPEED, SHOOT]


class Level11(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, HAPY, SAD_, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [GREY, None, GREY, None, GREY, None, GREY, None, GREY, None, GREY, None, GREY, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [BLOK, PINK, BLOK, PINK, BLOK, PINK, BLOK, PINK, BLOK, PINK, BLOK, PINK, BLOK, PINK],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, BLUL, BLOK, REDL, BLOK, BLUL, BLOK, REDL, BLOK, BLUL, BLOK, REDL, BLOK, BLUL],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
                     [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None]]

        self.icons = [LENGTHEN, MAGNET, SAFETY, SLOW, MAGNET, LENGTHEN, LIFE, LIFE]


class Level12(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, REDB, None, BONB, KNYA, None, REDB, None, None, None, None],
                     [AQUA, None, None, PINK, None, None, UK__, BONO, None, None, PINK, None, None, AQUA],
                     [None, None, REDB, None, None, None, BONN, KNYA, None, None, None, REDB, None, None],
                     [AQUA, None, None, PINK, None, None, UK__, BONU, None, None, PINK, None, None, AQUA],
                     [None, None, None, None, RGRY, None, BONS, KNYA, None, LGRY, None, None, None, None],
                     [AQUA, None, None, None, RGRY, None, None, None, None, LGRY, None, None, None, AQUA],
                     [None, None, None, None, MUL4, RGRY, MUL4, MUL4, LGRY, MUL4, None, None, None, None],
                     [AQUA, None, None, None, None, None, None, None, None, None, None, None, None, AQUA],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [BLUE, BLUE, None, None, None, None, None, None, None, None, None, None, BLUE, BLUE],
                     [BLUE, BLUE, None, None, None, MUL2, None, None, MUL2, None, None, None, BLUE, BLUE]]

        self.icons = [SLOW, SCORE, SPEED, SPLIT, LENGTHEN, LENGTHEN, LIFE]


class Level13(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, GREY, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, GREY, None, None, None, GRYL, GRYL, None, None, None, None, None, None],
                     [None, None, NWAL, None, None, GRYL, GRYL, GRYL, GRYL, None, None, None, None, None],
                     [None, None, NWAL, None, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, None, None, None, None],
                     [None, None, NWAL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, None, None, None],
                     [None, None, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, None, None],
                     [None, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, GRYL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, NWAL, RED_, RED_, RED_, RWAL, RWAL, RWAL, NWAL, RED_, RED_, RED_, NWAL, None],
                     [None, NWAL, RED_, HAPY, RED_, RWAL, RWAL, RWAL, NWAL, RED_, HAPY, RED_, NWAL, None],
                     [None, NWAL, RED_, RED_, RED_, RWAL, RWAL, RWAL, NWAL, RED_, RED_, RED_, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, NWAL, GRN_, GRN_, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, NWAL, GRN_, GRN_, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, NWAL, BLOK, BLOK, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, NWAL, GRN_, GRN_, RWAL, RWAL, RWAL, RWAL, NWAL, None],
                     [None, RWAL, RWAL, RWAL, RWAL, NWAL, GRN_, GRN_, RWAL, RWAL, RWAL, RWAL, NWAL, None]]

        self.icons = [LENGTHEN, SCORE, INVINCIBLE, SPLIT, LENGTHEN, SHORTEN, LENGTHEN, SHORTEN, LIFE,
                      SPLIT, SPEED]


class Level14(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, REDL, None],
                     [None, None, None, None, None, None, REDL, None, None, BLUE, None, REDL, GREY, REDL],
                     [None, None, REDL, None, None, REDL, BONO, REDL, None, BLUE, None, None, REDL, None],
                     [None, REDL, BONB, REDL, None, None, REDL, None, None, None, None, None, None, None],
                     [None, None, REDL, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, REDL, None, None, None, None],
                     [None, None, None, None, GRN_, GRN_, None, None, REDL, BONU, REDL, None, None, None],
                     [None, None, None, None, None, None, None, None, None, REDL, None, None, None, None],
                     [None, None, None, None, REDL, None, None, None, None, None, None, None, None, None],
                     [HAPY, HAPY, None, REDL, BONN, REDL, None, None, None, None, None, None, None, None],
                     [None, SAD_, SAD_, None, REDL, None, None, None, GRN_, GRN_, None, None, REDL, None],
                     [None, None, None, None, None, None, None, None, None, None, None, REDL, BONS, REDL],
                     [None, None, None, None, None, None, None, None, None, None, None, None, REDL, None],
                     [None, None, None, REDB, PINK, None, None, REDL, None, None, None, None, None, None],
                     [None, REDL, None, None, None, None, REDL, GRYL, REDL, None, None, None, None, None],
                     [REDL, GREY, REDL, None, None, None, None, REDL, None, None, None, None, None, None],
                     [None, REDL, None, None, HAPY, None, None, None, None, None, SAD_, None, None, None],
                     [None, None, None, None, SAD_, HAPY, SAD_, None, None, None, SAD_, HAPY, SAD_, None],
                     [None, None, None, None, None, HAPY, None, None, None, None, None, HAPY, None, None]]

        self.icons = [LENGTHEN, SCORE, ADVANCE, LENGTHEN, INVINCIBLE, LIFE, SPEED, SPLIT]


class Level15(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, AQUL, None, None, None, None, None, None, AQUL, None, None, None],
                     [None, None, REDL, NWAL, REDL, None, None, None, None, REDL, NWAL, REDL, None, None],
                     [None, BLUL, REDL, CUP_, REDL, AQUL, AQUL, AQUL, AQUL, REDL, CUP_, REDL, BLUL, None],
                     [BLUL, NWAL, REDL, NWAL, REDL, None, CUP_, CUP_, None, REDL, NWAL, REDL, NWAL, BLUL],
                     [BLUL, RWAL, NWAL, BLUL, None, NWAL, CUP_, CUP_, NWAL, None, BLUL, RWAL, NWAL, BLUL],
                     [AQUL, RWAL, NWAL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, RWAL, NWAL, AQUL],
                     [REDL, RWAL, NWAL, GRNL, None, NWAL, CUP_, CUP_, NWAL, None, GRNL, RWAL, NWAL, REDL],
                     [REDL, NWAL, BLUL, NWAL, BLUL, None, CUP_, CUP_, None, BLUL, NWAL, BLUL, NWAL, REDL],
                     [None, REDL, BLUL, CUP_, BLUL, GRNL, GRNL, GRNL, GRNL, BLUL, CUP_, BLUL, REDL, None],
                     [None, None, BLUL, NWAL, BLUL, None, None, None, None, BLUL, NWAL, BLUL, None, None],
                     [None, None, None, GRNL, None, None, None, None, None, None, GRNL, None, None, None]]

        self.icons = [LENGTHEN, SHOOT, SPLIT, SAFETY, SHORTEN, LENGTHEN, INVINCIBLE, SCORE, MAGNET]


class Level16(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, RWAL, NWAL, RED_, RED_, RWAL, NWAL, None, None, None, None],
                     [None, UK__, UK__, UK__, REDB, None, REDB, REDB, None, REDB, KNYA, KNYA, KNYA, None],
                     [REDB, None, None, None, CUP_, CUP_, BBB_, FNM_, CUP_, CUP_, None, None, None, REDB],
                     [None, None, None, None, None, GREY, None, None, GREY, None, None, None, None, None],
                     [None, None, None, GREY, GREY, RED_, None, None, BLUE, GREY, GREY, None, None, None],
                     [None, None, GREY, None, None, None, BLUE, RED_, None, None, None, GREY, None, None],
                     [None, None, GREY, None, None, None, RED_, BLUE, None, None, None, GREY, None, None],
                     [None, None, GREY, None, None, GRN_, None, None, GRN_, None, None, GREY, None, None],
                     [None, None, BONB, BONO, BONN, BONU, BONS, LGRY, LGRY, LGRY, LGRY, LGRY, None, None],
                     [None, MUL4, None, None, None, None, None, None, None, None, None, None, MUL4, None],
                     [MUL4, None, None, None, None, None, None, None, None, None, None, None, None, MUL4],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, MUL2, MUL1, MUL1, MUL2, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL]]

        self.icons = [LENGTHEN, SHOOT, SAFETY, MAGNET, ADVANCE, LIFE, SCORE, SHORTEN, SPEED, SLOW]


class Level17(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None],
                     [None, None, None, None, None, None, BLUE, BLUE, None, None, None, None, None, None],
                     [None, None, None, None, KNYA, KNYA, None, None, UK__, UK__, None, None, None, None],
                     [None, None, None, None, REDL, REDL, None, None, REDL, REDL, None, None, None, None],
                     [None, None, BLUE, BLUE, None, None, None, None, None, None, BLUE, BLUE, None, None],
                     [None, None, BLUE, BLUE, None, None, None, None, None, None, BLUE, BLUE, None, None],
                     [None, None, None, None, GRNL, GRNL, None, None, GRNL, GRNL, None, None, None, None],
                     [None, None, None, None, GRNL, BLOK, None, None, BLOK, GRNL, None, None, None, None],
                     [None, None, None, None, None, None, AQUA, AQUA, None, None, None, None, None, None],
                     [None, None, None, None, None, None, AQUA, AQUA, None, None, None, None, None, None],
                     [None, None, None, None, GRNL, BLOK, None, None, BLOK, GRNL, None, None, None, None],
                     [None, None, None, None, GRNL, GRNL, None, None, GRNL, GRNL, None, None, None, None],
                     [None, None, BLUE, BLUE, None, None, None, None, None, None, BLUE, BLUE, None, None],
                     [None, None, BLUE, BLUE, None, None, None, None, None, None, BLUE, BLUE, None, None],
                     [GREY, RGRY, None, None, REDL, REDL, None, None, REDL, REDL, None, None, LGRY, GREY],
                     [RGRY, GREY, None, None, CUP_, FNM_, None, None, BBB_, CUP_, None, None, GREY, LGRY]]

        self.icons = [INVINCIBLE, SPEED, SCORE, SHOOT, SAFETY, LENGTHEN, MAGNET, SLOW]


class Level18(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, REDL, None, None, None, None, REDL, None, None, None, None],
                     [None, None, None, REDL, GRNL, None, None, None, None, GRNL, REDL, None, None, None],
                     [None, None, None, GRNL, GRNL, None, None, None, None, GRNL, GRNL, None, None, None],
                     [None, None, None, GRNL, BLUL, None, None, None, None, BLUL, GRNL, None, None, None],
                     [None, None, None, BLUL, AQUL, None, BLUL, BLUL, None, AQUL, BLUL, None, None, None],
                     [None, None, None, AQUL, AQUL, BLUL, RED_, RED_, BLUL, AQUL, AQUL, None, None, None],
                     [None, None, None, BLUL, AQUL, None, BLUL, BLUL, None, AQUL, BLUL, None, None, None],
                     [None, None, None, GRNL, BLUL, None, None, None, None, BLUL, GRNL, None, None, None],
                     [None, None, None, GRNL, GRNL, None, None, None, None, GRNL, GRNL, None, None, None],
                     [None, None, None, REDL, GRNL, None, None, None, None, GRNL, REDL, None, None, None],
                     [BLOK, None, None, None, REDL, None, None, None, None, REDL, None, None, None, BLOK],
                     [None, MUL4, None, None, None, None, None, None, None, None, None, None, MUL4, None],
                     [None, None, BLOK, None, None, None, None, None, None, None, None, BLOK, None, None],
                     [None, None, None, BLOK, None, None, None, None, None, None, BLOK, None, None, None],
                     [None, None, None, None, BLOK, None, None, None, None, BLOK, None, None, None, None],
                     [None, None, None, None, None, BLOK, BLOK, BLOK, BLOK, None, None, None, None, None],
                     [None, None, None, None, None, BLOK, RED_, RED_, BLOK, None, None, None, None, None],
                     [None, None, None, None, None, BLOK, MUL4, MUL4, BLOK, None, None, None, None, None]]

        self.icons = [SLOW, MAGNET, LIFE, LENGTHEN, SPEED, SPEED, SCORE, SAFETY, SAFETY, LIFE]


class Level19(Level):
    def populate_grid_and_icons(self):
        self.grid = [[REDL, GRYL, None, None, None, None, None, None, None, None, None, None, GRYL, REDL],
                     [None, REDL, BLUL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, BLUL, REDL, None],
                     [None, None, REDL, BLUL, None, None, None, None, None, None, BLUL, REDL, None, None],
                     [None, None, None, REDL, BLUL, None, None, None, None, BLUL, REDL, None, None, None],
                     [None, None, None, None, REDL, PINK, None, None, PINK, REDL, None, None, None, None],
                     [None, None, None, None, None, REDL, BLUL, BLUL, REDL, None, None, None, None, None],
                     [None, None, None, None, None, GRYL, UK__, KNYA, GRYL, None, None, None, None, None],
                     [None, None, None, None, None, GRYL, KNYA, UK__, GRYL, None, None, None, None, None],
                     [None, None, None, None, None, REDL, BLUL, BLUL, REDL, None, None, None, None, None],
                     [None, None, None, None, REDL, PINK, None, None, PINK, REDL, None, None, None, None],
                     [None, None, None, REDL, BLUL, None, None, None, None, BLUL, REDL, None, None, None],
                     [None, None, REDL, BLUL, None, None, None, None, None, None, BLUL, REDL, None, None],
                     [None, REDL, BLUL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, BLUL, REDL, None],
                     [REDL, GRYL, None, None, None, None, None, None, None, None, None, None, GRYL, REDL]]

        self.icons = [SPLIT, INVINCIBLE, ADVANCE, LIFE, SCORE, SHORTEN, SPEED, SLOW]


class Level20(Level):
    def populate_grid_and_icons(self):
        self.grid = [[SAD_, SAD_, None, None, CUP_, None, None, None, None, CUP_, None, None, SAD_, SAD_],
                     [SAD_, None, None, CUP_, CUP_, CUP_, None, None, CUP_, CUP_, CUP_, None, None, SAD_],
                     [None, None, None, None, CUP_, None, None, None, None, CUP_, None, None, None, None],
                     [None, None, None, None, None, MUL4, MUL4, MUL4, MUL4, None, None, None, None, None],
                     [None, None, None, None, None, MUL4, PINK, PINK, MUL4, None, None, None, None, None],
                     [None, None, BBB_, None, None, MUL4, RED_, RED_, MUL4, None, None, FNM_, None, None],
                     [None, BBB_, REDB, BBB_, None, MUL4, RED_, RED_, MUL4, None, FNM_, REDB, FNM_, None],
                     [None, BBB_, REDB, BBB_, None, MUL4, RED_, RED_, MUL4, None, FNM_, REDB, FNM_, None],
                     [None, None, BBB_, None, None, MUL4, RED_, RED_, MUL4, None, None, FNM_, None, None],
                     [None, None, None, None, None, MUL4, PINK, PINK, MUL4, None, None, None, None, None],
                     [None, None, None, None, None, MUL4, MUL4, MUL4, MUL4, None, None, None, None, None],
                     [None, None, None, None, CUP_, None, None, None, None, CUP_, None, None, None, None],
                     [SAD_, None, None, CUP_, CUP_, CUP_, None, None, CUP_, CUP_, CUP_, None, None, SAD_],
                     [SAD_, SAD_, None, None, CUP_, None, None, None, None, CUP_, None, None, SAD_, SAD_]]

        self.icons = [LENGTHEN, INVINCIBLE, SPLIT, SHOOT, LENGTHEN, SHORTEN, MAGNET, SHOOT]


class Level21(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, HAPY, None, None, None, None, HAPY, HAPY, None, None, None, None, HAPY, None],
                     [None, SAD_, REDL, None, None, None, KNYA, REDL, None, None, None, REDL, SAD_, None],
                     [None, None, KNYA, REDL, None, None, REDL, UK__, None, None, REDL, UK__, None, None],
                     [None, None, None, REDL, REDL, None, KNYA, REDL, None, REDL, REDL, None, None, None],
                     [None, None, None, None, KNYA, REDL, REDL, UK__, REDL, UK__, None, None, None, None],
                     [None, None, None, None, None, REDL, None, None, REDL, None, None, None, None, None],
                     [HAPY, REDL, KNYA, REDL, KNYA, None, PINK, PINK, None, UK__, REDL, UK__, REDL, HAPY],
                     [SAD_, KNYA, REDL, KNYA, REDL, None, PINK, PINK, None, REDL, UK__, REDL, UK__, SAD_],
                     [None, None, None, None, None, REDL, None, None, REDL, None, None, None, None, None],
                     [None, None, None, None, KNYA, REDL, REDL, UK__, REDL, UK__, None, None, None, None],
                     [None, None, None, REDL, REDL, None, KNYA, REDL, None, REDL, REDL, None, None, None],
                     [None, None, KNYA, REDL, None, None, REDL, UK__, None, None, REDL, UK__, None, None],
                     [None, HAPY, REDL, None, None, None, KNYA, REDL, None, None, None, REDL, HAPY, None],
                     [None, SAD_, None, None, None, None, SAD_, SAD_, None, None, None, None, SAD_, None]]

        self.icons = [LIFE, SHOOT, SPLIT, SLOW, INVINCIBLE, LENGTHEN, SPEED, SCORE, SHORTEN]


class Level22(Level):
    def populate_grid_and_icons(self):
        self.grid = [[REDB, None, None, REDB, None, GRN_, None, None, GRN_, None, REDB, None, None, REDB],
                     [REDB, REDB, REDB, REDB, None, GRN_, GRN_, GRN_, GRN_, None, REDB, REDB, REDB, REDB],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, None, None, None],
                     [GRN_, GRN_, None, AQUA, None, None, None, None, None, None, AQUA, None, GRN_, GRN_],
                     [None, GRN_, None, RED_, None, None, None, None, None, None, RED_, None, GRN_, None],
                     [None, GRN_, None, None, None, RED_, None, None, RED_, None, None, None, GRN_, None],
                     [None, GRN_, None, None, None, AQUA, AQUA, AQUA, AQUA, None, None, None, GRN_, None],
                     [None, GRN_, None, None, None, RED_, None, None, RED_, None, None, None, GRN_, None],
                     [None, GRN_, None, RED_, None, None, None, None, None, None, RED_, None, GRN_, None],
                     [GRN_, GRN_, None, AQUA, None, None, None, None, None, None, AQUA, None, GRN_, GRN_],
                     [None, None, None, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [REDB, REDB, REDB, REDB, None, GRN_, GRN_, GRN_, GRN_, None, REDB, REDB, REDB, REDB],
                     [REDB, None, None, REDB, None, GRN_, None, None, GRN_, None, REDB, None, None, REDB]]

        self.icons = [LENGTHEN, LENGTHEN, SAFETY, SLOW, SPEED, ADVANCE, SCORE, SHORTEN, SHOOT]


class Level23(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, MUL4, MUL4, None, None, None, None, None, None],
                     [None, None, None, None, None, GREY, REDL, REDL, GREY, None, None, None, None, None],
                     [None, None, None, None, GREY, BLUL, CUP_, CUP_, BLUL, GREY, None, None, None, None],
                     [None, None, None, GREY, BLUL, CUP_, CUP_, CUP_, CUP_, BLUL, GREY, None, None, None],
                     [None, None, GREY, GRNL, GRNL, BBB_, BBB_, BBB_, BBB_, GRNL, GRNL, GREY, None, None],
                     [NWAL, BONS, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL, GREY, NWAL],
                     [None, None, BONU, GRNL, GRNL, FNM_, FNM_, FNM_, FNM_, GRNL, GRNL, GREY, None, None],
                     [None, None, None, BONN, BLUL, CUP_, CUP_, CUP_, CUP_, BLUL, GREY, None, None, None],
                     [None, None, None, None, BONO, BLUL, CUP_, CUP_, BLUL, GREY, None, None, None, None],
                     [None, None, None, None, None, BONB, REDL, REDL, GREY, None, None, None, None, None],
                     [None, None, None, None, None, None, MUL4, MUL4, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, GRN_, None, GRN_, None, None, None, None, GRN_, None, GRN_, None, None],
                     [None, None, None, GRN_, None, None, None, None, None, None, GRN_, None, None, None],
                     [None, None, GRN_, None, GRN_, None, None, None, None, GRN_, None, GRN_, None, None],
                     [None, GRN_, None, GRN_, None, GRN_, None, None, GRN_, None, GRN_, None, GRN_, None],
                     [PINK, None, GRN_, None, GRN_, None, PINK, PINK, None, GRN_, None, GRN_, None, PINK]]

        self.icons = [SHOOT, LENGTHEN, SCORE, SPLIT, INVINCIBLE, SPEED, SHORTEN, SHORTEN, LIFE]


class Level24(Level):
    def populate_grid_and_icons(self):
        self.grid = [[REDB, REDB, None, None, None, None, PINK, PINK, None, None, None, None, REDB, REDB],
                     [REDB, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, REDB],
                     [None, None, None, None, AQUL, GRNL, REDL, REDL, GRNL, AQUL, None, None, None, None],
                     [None, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, None],
                     [None, None, None, PINK, PINK, None, PINK, PINK, None, PINK, PINK, None, None, None],
                     [None, None, AQUL, None, REDL, RGRY, None, None, LGRY, REDL, None, AQUL, None, None],
                     [None, AQUL, None, REDL, None, None, AQUL, AQUL, None, None, REDL, None, AQUL, None],
                     [PINK, PINK, REDL, GRNL, REDL, AQUL, BLOK, BLOK, AQUL, REDL, GRNL, REDL, PINK, PINK],
                     [None, AQUL, None, REDL, None, None, AQUL, AQUL, None, None, REDL, None, AQUL, None],
                     [None, None, AQUL, None, REDL, RGRY, None, None, LGRY, REDL, None, AQUL, None, None],
                     [None, None, None, PINK, PINK, None, PINK, PINK, None, PINK, PINK, None, None, None],
                     [None, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, None],
                     [None, None, None, None, AQUL, GRNL, REDL, REDL, GRNL, AQUL, None, None, None, None],
                     [REDB, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, REDB],
                     [REDB, REDB, None, None, None, None, PINK, PINK, None, None, None, None, REDB, REDB]]

        self.icons = [INVINCIBLE, SHOOT, SAFETY, SCORE, SPEED, SLOW, LENGTHEN, SHOOT, SHORTEN, SPEED,
                      MAGNET, LIFE]


class Level25(Level):
    def populate_grid_and_icons(self):
        self.grid = [[REDL, PINK, None, None, None, HAPY, None, None, HAPY, None, None, None, PINK, REDL],
                     [REDL, None, GREY, GREY, None, None, HAPY, HAPY, None, None, GREY, GREY, None, REDL],
                     [None, None, None, None, GREY, HAPY, None, None, HAPY, GREY, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, REDL, None, None, GRNL, None, None, GRNL, None, None, BLUL, None, None],
                     [None, REDL, CUP_, BLUL, None, None, GRNL, GRNL, None, None, BLUL, CUP_, REDL, None],
                     [None, BLUL, CUP_, REDL, None, None, GRNL, GRNL, None, None, REDL, CUP_, BLUL, None],
                     [None, None, REDL, None, None, GRNL, None, None, GRNL, None, None, BLUL, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, BLOK, BLOK, BLOK, BLOK, BLOK, BLOK, None, None, None, None],
                     [None, None, None, BLOK, BLUL, REDL, BLUL, REDL, BLUL, REDL, BLOK, None, None, None],
                     [None, None, BLOK, BLUL, REDL, BLUL, REDL, BLUL, REDL, BLUL, REDL, BLOK, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, PINK, PINK, None, None, None, None, None, None],
                     [None, None, None, None, None, None, PINK, PINK, None, None, None, None, None, None]]

        self.icons = [LIFE, SPEED, LENGTHEN, INVINCIBLE, SPLIT, MAGNET, SCORE, SHORTEN, SLOW, ADVANCE]


class Level26(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, GRN_, None, GRN_, None, None, None, None, RED_, None, None, None, None, None],
                     [RED_, None, None, None, RED_, None, None, GRN_, HAPY, GRN_, None, None, None, None],
                     [RED_, None, None, None, RED_, None, None, None, RED_, None, None, None, GRN_, None],
                     [None, RED_, None, RED_, None, None, None, None, None, None, None, RED_, None, None],
                     [None, RED_, None, RED_, None, None, None, None, None, None, GRN_, None, None, None],
                     [None, None, BBB_, None, None, None, None, None, None, RED_, None, None, None, SAD_],
                     [None, None, CUP_, None, None, None, None, None, GRN_, None, None, None, SAD_, None],
                     [None, None, BBB_, None, None, None, None, RED_, None, None, None, None, None, None],
                     [GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY],
                     [None, None, None, None, None, None, GRN_, None, None, None, None, FNM_, None, None],
                     [None, HAPY, None, None, None, RED_, None, None, None, None, None, CUP_, None, None],
                     [HAPY, None, None, None, GRN_, None, None, None, None, None, None, FNM_, None, None],
                     [None, None, None, RED_, None, None, None, None, None, None, GRN_, None, GRN_, None],
                     [None, None, GRN_, None, None, None, None, None, None, None, GRN_, None, GRN_, None],
                     [None, RED_, None, None, None, GRN_, None, None, None, GRN_, None, None, None, GRN_],
                     [None, None, None, None, RED_, SAD_, RED_, None, None, GRN_, None, None, None, GRN_],
                     [None, None, None, None, None, GRN_, None, None, None, None, RED_, None, RED_, None]]

        self.icons = [LENGTHEN, SHORTEN, SHORTEN, SPEED, SLOW, SCORE, SPLIT, SPEED, SAFETY]


class Level27(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, RED_, RED_, AQUA, AQUA, None, None, None, None, None],
                     [None, None, None, None, GRYL, None, None, None, None, GRYL, None, None, None, None],
                     [None, None, None, BLUE, None, None, AQUA, RED_, None, None, GRN_, None, None, None],
                     [None, None, None, BLUE, None, GRN_, None, None, BLUE, None, GRN_, None, None, None],
                     [None, None, None, GRN_, None, BLUE, None, None, GRN_, None, BLUE, None, None, None],
                     [None, None, None, GRN_, None, None, RED_, AQUA, None, None, BLUE, None, None, None],
                     [None, None, None, None, GRYL, None, None, None, None, GRYL, None, None, None, None],
                     [None, None, None, None, None, AQUA, AQUA, RED_, RED_, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [RGRY, GRN_, REDB, GRN_, REDB, GRN_, REDB, REDB, GRN_, REDB, GRN_, REDB, GRN_, LGRY],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [RGRY, None, None, GRN_, PINK, GRN_, PINK, PINK, GRN_, PINK, GRN_, None, None, LGRY],
                     [None, None, HAPY, None, None, None, None, None, None, None, None, HAPY, None, None],
                     [RGRY, None, None, None, None, GRN_, REDB, REDB, GRN_, None, None, None, None, LGRY],
                     [None, None, HAPY, None, CUP_, None, None, None, None, CUP_, None, HAPY, None, None],
                     [BLOK, BLOK, BLOK, BLOK, BLOK, BLOK, MUL4, MUL4, BLOK, BLOK, BLOK, BLOK, BLOK, BLOK],
                     [BLOK, BLOK, BLOK, BLOK, BLOK, BLOK, MUL4, MUL4, BLOK, BLOK, BLOK, BLOK, BLOK, BLOK]]

        self.icons = [MAGNET, LIFE, SAFETY, LENGTHEN, MAGNET, LENGTHEN, SPEED, SHORTEN, SCORE, ADVANCE,
                      SPLIT, SLOW, LIFE]


class Level28(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, RGRY, None, None, None, MUL4, None, None, MUL4, None, None, None, LGRY, None],
                     [BLUL, None, REDL, RGRY, MUL4, None, None, None, None, MUL4, LGRY, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, None, None, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, None, None, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, HAPY, HAPY, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, SAD_, SAD_, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, None, None, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, None, None, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, MUL4, None, None, None, None, None, None, MUL4, REDL, None, BLUL],
                     [None, RGRY, None, MUL4, None, None, None, None, None, None, MUL4, None, LGRY, None],
                     [BLUL, None, REDL, RGRY, MUL4, None, None, None, None, MUL4, LGRY, REDL, None, BLUL],
                     [REDB, REDB, REDB, REDB, REDB, MUL4, None, None, MUL4, REDB, REDB, REDB, REDB, REDB]]

        self.icons = [SHOOT, INVINCIBLE, SCORE, SPLIT, SPEED, LIFE, SHOOT, SCORE, LENGTHEN, SHORTEN,
                      SPEED, SHORTEN]


class Level29(Level):
    def populate_grid_and_icons(self):
        self.grid = [[None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, BONO, REDL, REDL, BLUL, None, None, None, None, BONN, REDL, REDL, BLUL, None],
                     [None, REDL, None, None, REDL, None, BLUE, BLUE, None, REDL, None, None, REDL, None],
                     [None, REDL, RWAL, NWAL, REDL, None, BLUE, None, None, REDL, RWAL, NWAL, REDL, None],
                     [None, REDL, None, None, REDL, None, BLUE, None, None, REDL, None, None, REDL, None],
                     [None, BLUL, REDL, REDL, BLUL, None, None, None, None, BLUL, REDL, REDL, BLUL, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, None, None, BONS, REDL, REDL, AQUL, None, None, None, None, None],
                     [None, None, BLUE, None, None, REDL, None, None, REDL, None, BLUE, BLUE, None, None],
                     [None, None, BLUE, BLUE, None, REDL, None, None, REDL, None, None, BLUE, None, None],
                     [None, None, None, None, None, REDL, None, None, REDL, None, None, None, None, None],
                     [None, None, None, None, None, AQUL, REDL, REDL, AQUL, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, BONB, REDL, REDL, GRNL, None, None, None, None, BONU, REDL, REDL, GRNL, None],
                     [None, REDL, None, None, REDL, None, None, BLUE, None, REDL, None, None, REDL, None],
                     [None, REDL, RWAL, NWAL, REDL, None, None, BLUE, None, REDL, RWAL, NWAL, REDL, None],
                     [None, REDL, None, None, REDL, None, BLUE, BLUE, None, REDL, None, None, REDL, None],
                     [None, GRNL, REDL, REDL, GRNL, None, None, None, None, GRNL, REDL, REDL, GRNL, None]]

        self.icons = [INVINCIBLE, SPEED, MAGNET, LENGTHEN, SPLIT, LIFE, SHORTEN, SCORE, SPLIT]


class Level30(Level):
    def populate_grid_and_icons(self):
        self.grid = [[REDL, None, None, None, None, None, REDL, REDL, None, None, None, None, None, REDL],
                     [CUP_, REDL, AQUL, AQUL, AQUL, REDL, BLUL, GRNL, REDL, AQUL, AQUL, AQUL, REDL, CUP_],
                     [BBB_, AQUL, RGRY, RGRY, RGRY, AQUL, GRNL, BLUL, AQUL, LGRY, LGRY, LGRY, AQUL, FNM_],
                     [CUP_, FNM_, REDL, AQUL, REDL, None, BLUL, GRNL, None, REDL, AQUL, REDL, BBB_, CUP_],
                     [AQUL, REDL, AQUL, CUP_, AQUL, None, GRNL, BLUL, None, AQUL, CUP_, AQUL, REDL, AQUL],
                     [None, AQUL, None, REDL, None, None, BLUL, GRNL, None, None, REDL, None, AQUL, None],
                     [REDL, None, None, None, REDL, AQUL, AQUL, AQUL, AQUL, REDL, None, None, None, REDL],
                     [None, None, None, None, None, REDL, GRNL, BLUL, REDL, None, None, None, None, None],
                     [None, None, None, None, None, None, REDL, REDL, None, None, None, None, None, None],
                     [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
                     [None, None, None, MUL4, MUL4, None, None, None, None, MUL4, MUL4, None, None, None],
                     [None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, None, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, None, None, MUL4, None, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, None, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None, MUL4, None, None],
                     [None, None, None, MUL4, MUL4, None, None, None, None, MUL4, MUL4, None, None, None]]

        self.icons = [SHORTEN, LENGTHEN, SCORE, SCORE, SHOOT, SHOOT, SPEED, SAFETY, SHORTEN, INVINCIBLE,
                      SPEED, LENGTHEN, SPEED, LIFE]


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             GAME VIEWS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class BouncingIntroView(arcade.View):
    """
    Introduces the game intro and level views by bouncing several times
    """

    def __init__(self, view: Union[Level, GameIntroView]):
        super().__init__()

        self.view = view

        self.bottom = -SCREEN_HEIGHT
        self.change_y = 2
        self.bounce_count = 0
        self.elapsed_time = 0

        # Sounds
        self.bounce_sound_1 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/bounce_1.wav")
        self.bounce_sound_2 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/bounce_2.wav")
        self.level_intro_whoosh_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/whoosh_2.wav")

        # Only load the level intro voice in a level because in GameIntroView,
        # level number is 0
        if isinstance(self.view, Level):
            self.level_intro_voice = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/level_"
                                                  f"{self.view.window.level_number}_voice.wav")

        self.first_whoosh_sound_played = False
        self.second_whoosh_sound_played = False

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_update(self, delta_time: float):
        """
        Bouncing logic
        """
        self.elapsed_time += delta_time

        # Pause for a while before bouncing in a level view
        if isinstance(self.view, GameIntroView) or isinstance(self.view, Level) and \
                self.elapsed_time > PAUSE_TIME + TRANSITION_TIME * 2:
            self.bottom += self.change_y
            self.change_y += GRAVITY

            # See if we hit the bottom
            if self.bottom >= 0:
                self.change_y *= -VELOCITY_RETAINED
                self.bounce_count += 1

                # If we reach the set number of bounces, return to the view
                if self.bounce_count == MAX_BOUNCES:
                    self.bottom = 0  # To reset the viewport as we exit this method
                    self.bounce_sound_2.play(volume=NORMAL_VOLUME)
                    self.window.show_view(self.view)
                else:
                    self.bounce_sound_1.play(volume=NORMAL_VOLUME)

        arcade.set_viewport(0, SCREEN_WIDTH, self.bottom, self.bottom + SCREEN_HEIGHT)

    def on_draw(self):
        self.view.on_draw()

        # Only draw this when we are in a level
        if isinstance(self.view, Level) and TRANSITION_TIME <= self.elapsed_time < PAUSE_TIME + TRANSITION_TIME:
            arcade.draw_scaled_texture_rectangle(SCREEN_WIDTH / 2, -SCREEN_HEIGHT / 2,
                                                 self.view.level_info_boundary)
            arcade.draw_text(f"Level {self.view.window.level_number:02}", SCREEN_WIDTH / 2,
                             -SCREEN_HEIGHT / 2, **LEVEL_INFO_TEXT)

            # Play the first whoosh sound and voice as we start displaying the level info text
            if not self.first_whoosh_sound_played:
                self.level_intro_whoosh_sound.play(volume=NORMAL_VOLUME)
                self.level_intro_voice.play(volume=NORMAL_VOLUME)
                self.first_whoosh_sound_played = True

        # Play the second whoosh sound as we stop displaying level info text
        elif isinstance(self.view, Level) and self.elapsed_time >= PAUSE_TIME + TRANSITION_TIME:
            if not self.second_whoosh_sound_played:
                self.level_intro_whoosh_sound.play(volume=NORMAL_VOLUME)
                self.second_whoosh_sound_played = True


class LevelOutroView(arcade.View):
    """
    Exits a level by moving the screen up. Then initiates a new level
    if one exists
    """

    def __init__(self, level: Level):
        super().__init__()

        self.level = level
        self.bottom = 0
        self.change_y = 2
        self.level_up_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/level_up_sound.wav")

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.level_up_sound.play(volume=NORMAL_VOLUME)

    def on_update(self, delta_time: float):
        """
        Movement logic
        """
        self.bottom += self.change_y
        self.change_y += GRAVITY

        # Once we move out of view, try and load the next level
        # (Screen height * 2 allows some pausing time before loading next level)
        if self.bottom >= SCREEN_HEIGHT * 2:
            try:
                level = eval(f"Level{self.level.window.level_number + 1}(self.window)")
                self.window.show_view(level)

            # Next level does not exist
            except NameError:
                # Check if we can get into the high scores list
                if self.level.window.score > HIGH_SCORES[-1].score:
                    self.window.show_view(NameEntryView(self.window))
                else:
                    self.window.show_view(HighScoreView(self.window))

                WHOOSH_SOUND.play(volume=NORMAL_VOLUME)
                self.bottom = 0  # To reset the viewport as we exit this method

        arcade.set_viewport(0, SCREEN_WIDTH, self.bottom, self.bottom + SCREEN_HEIGHT)

    def on_draw(self):
        self.level.on_draw()


class FullscreenView(arcade.View):
    """
    Base class for fullscreen views
    """

    def __init__(self, window: ParanoidGame):
        super().__init__()
        self.window = window

        self.boundary = FullscreenBoundary()
        self.ball_list = arcade.SpriteList()
        self.brick_list = arcade.SpriteList(use_spatial_hash=True, is_static=True)

        # Override in sub-classes
        self.background_music: Optional[arcade.Sound] = None

    def add_random_balls(self):
        """
        Adds balls at random points, ensuring they are not place on top of a brick
        """
        for i in range(RANDOM_BALLS):
            placed_successfully = False
            ball = assets.NormalBall(self.boundary, self.brick_list)

            # Randomize ball velocity directions
            ball.velocity_angle = random.randrange(45, 60)
            ball.set_velocity()

            while not placed_successfully:
                ball.center_x = random.randrange(self.boundary.inner_left + int(ball.width),
                                                 self.boundary.inner_right - int(ball.width))
                ball.center_y = random.randrange(self.boundary.inner_bottom + int(ball.height),
                                                 self.boundary.inner_top - int(ball.height))

                if not ball.collides_with_list(self.brick_list) and \
                        not ball.collides_with_list(self.ball_list):
                    placed_successfully = True

                    # Create random movement by setting some balls to move in opposite direction
                    if i % 2 == 0:
                        ball.change_x *= -1
                        ball.change_y *= -1

                    self.ball_list.append(ball)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        self.background_music.stop()

    def on_update(self, delta_time: float):
        """
        Update the balls' positions
        """
        self.ball_list.on_update()

        # Loop the background music
        if self.background_music.get_stream_position() == 0:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        arcade.start_render()

        self.boundary.draw()
        self.brick_list.draw()
        self.ball_list.draw()


class GameIntroView(FullscreenView):
    """
    Starting screen of the game
    """

    def __init__(self, window: ParanoidGame):
        super().__init__(window)

        self.first_time_showing = True
        self.brick_list.append(assets.ParanoidIntroBrick(center_x=SCREEN_WIDTH / 2,
                                                         center_y=SCREEN_HEIGHT / 2))
        self.add_random_balls()

        self.elapsed_time = 0
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/game_intro_music.mp3",
                                             streaming=True)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

        if self.first_time_showing:
            self.first_time_showing = False
            self.window.show_view(BouncingIntroView(self))
        else:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_update(self, delta_time: float):
        super().on_update(delta_time)

        self.elapsed_time += delta_time
        if self.elapsed_time > PAUSE_TIME * 3:
            self.window.show_view(MainMenuView(self.window))

    def on_key_press(self, symbol: int, modifiers: int):
        # Fast-forward/skip
        if symbol == arcade.key.ENTER or symbol == arcade.key.SPACE:
            self.window.show_view(MainMenuView(self.window))


class MainMenuView(FullscreenView):
    """
    Main menu
    """

    def __init__(self, window: ParanoidGame):
        super().__init__(window)

        self.selected = 0
        self.elapsed_time = 0
        self.options = ["New Game", "How To Play", "High Scores", "Quit"]
        self.brick_list.append(assets.MenuBrick(center_x=SCREEN_WIDTH / 2,
                                                center_y=SCREEN_HEIGHT / 2))
        self.add_random_balls()
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/main_menu_music.mp3",
                                             streaming=True)

    def on_update(self, delta_time: float):
        """
        Demo level logic
        """
        super().on_update(delta_time)
        self.elapsed_time += delta_time

        # If we have paused for enough time, display a random demo level
        if self.elapsed_time > DEMO_LEVEL_TIME / 2:
            level_number = random.randrange(1, 31)  # Include level 30 TODO: Generalize this (not 30, 31, etc)
            level = eval(f"Level{level_number}(self.window, is_demo_level=True)")
            self.window.show_view(level)
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        super().on_draw()

        # Draw main menu heading
        arcade.draw_text("Main Menu", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 250, **MENU_TEXT_HEADING)

        # Selection options
        for index, text in enumerate(self.options):
            if index == self.selected:
                style = MENU_TEXT_SELECTED
            else:
                style = MENU_TEXT_NORMAL

            arcade.draw_text(text, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 350 - index * 85, **style)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.DOWN:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected += 1
            if self.selected >= len(self.options):
                self.selected = 0

        elif symbol == arcade.key.UP:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected -= 1
            if self.selected < 0:
                self.selected = len(self.options) - 1

        elif symbol == arcade.key.ENTER:
            ENTER_SOUND.play(volume=NORMAL_VOLUME)

            # New game
            if self.selected == 0:
                self.window.reset_game()
                self.window.show_view(Level1(self.window))

            # How to play
            elif self.selected == 1:
                self.window.show_view(HowToPlayView(self))

            # High scores
            elif self.selected == 2:
                self.window.show_view(HighScoreView(self.window))

            # Quit
            elif self.selected == 3:
                self.window.show_view(QuitGameConfirmationView(self))

        self.elapsed_time = 0  # Reset the elapsed time on every key press


class HighScoreView(FullscreenView):
    """
    Shows the scores leader-board
    """

    def __init__(self, window: ParanoidGame, new_high_score=False):
        super().__init__(window)
        self.new_high_score = new_high_score

        spacing = 60  # pixels

        # Create and position leader board brick
        self.leader_board_brick = assets.LeaderBoardBrick(center_x=SCREEN_WIDTH / 2)
        self.leader_board_brick.top = self.boundary.inner_top - spacing
        self.brick_list.append(self.leader_board_brick)

        # Create and position high scores brick
        self.high_scores_brick = assets.HighScoresBrick(center_x=SCREEN_WIDTH / 2)
        self.high_scores_brick.top = self.boundary.inner_top - self.leader_board_brick.height - spacing * 2
        self.brick_list.append(self.high_scores_brick)

        self.add_random_balls()
        self.new_high_score_voice = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/high_score_voice.wav")
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/high_scores_music.mp3",
                                             streaming=True)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=LOW_VOLUME)

        # If there is a new high score, play the high score voice
        if self.new_high_score:
            self.new_high_score_voice.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        super().on_draw()

        arcade.draw_text("Leader Board", SCREEN_WIDTH / 2, self.leader_board_brick.center_y,
                         **LEADER_BOARD_HEADING)
        arcade.draw_text("Name", self.high_scores_brick.left + 160, self.high_scores_brick.top - 40,
                         **HIGH_SCORES_HEADING)
        arcade.draw_text("Level", self.high_scores_brick.right - 320, self.high_scores_brick.top - 40,
                         **HIGH_SCORES_HEADING)
        arcade.draw_text("Score", self.high_scores_brick.right - 120, self.high_scores_brick.top - 40,
                         **HIGH_SCORES_HEADING)

        # Use index for positioning text
        for index, entry in enumerate(HIGH_SCORES):
            arcade.draw_text(f"{index + 1}", self.high_scores_brick.left + 60,
                             self.high_scores_brick.top - 90 - 40 * index, **HIGH_SCORES_NUMBERS)
            arcade.draw_text(entry.name, self.high_scores_brick.left + 110,
                             self.high_scores_brick.top - 90 - 40 * index, **HIGH_SCORES_NAMES)
            arcade.draw_text(entry.level, self.high_scores_brick.right - 300,
                             self.high_scores_brick.top - 90 - 40 * index, **HIGH_SCORES_NUMBERS)
            arcade.draw_text(f"{entry.score:,}", self.high_scores_brick.right - 60,
                             self.high_scores_brick.top - 90 - 40 * index, **HIGH_SCORES_NUMBERS)

    def on_key_press(self, symbol: int, modifiers: int):
        # Enter or Escape
        if symbol == arcade.key.ENTER or symbol == arcade.key.ESCAPE:
            self.window.show_view(MainMenuView(self.window))


class NameEntryView(arcade.View):
    """
    View for entering player's name if there is a new high score
    """

    def __init__(self, window: ParanoidGame):
        super().__init__()
        self.window = window

        self.ui_manager = UIManager()
        self.ui_manager.purge_ui_elements()

        self.name_entry_box = UIInputBox(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 450, 50)
        self.name_entry_box.set_style_attrs(font_name=BGOTHL, font_size=30,
                                            font_color=arcade.color.WHITE,
                                            font_color_hover=arcade.color.WHITE,
                                            font_color_focus=arcade.color.WHITE,
                                            border_color=arcade.color.WHITE,
                                            border_color_hover=arcade.color.WHITE,
                                            border_color_focus=arcade.color.WHITE,
                                            bg_color_=arcade.color.BLACK,
                                            bg_color_hover=arcade.color.BLACK,
                                            bg_color_focus=arcade.color.BLACK,
                                            vmargin=10, margin_left=5)
        self.name_entry_box._focused = True  # Set it to always focus
        self.ui_manager.add_ui_element(self.name_entry_box)

        self.border_list = arcade.SpriteList(is_static=True)
        self.border_list.append(arcade.Sprite(f"{IMAGES_BASE_PATH}/boundaries/confirmation_dialogue_boundary.png",
                                              center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT / 2))
        self.invalid_name_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/invalid_name_tone.wav")

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_hide_view(self):
        WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        arcade.start_render()  # GUI elements are automatically drawn

        self.border_list.draw()
        arcade.draw_text("Enter your name", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 80,
                         **ENTER_NAME_HEADING)
        arcade.draw_text("Max: 15 characters", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                         **BONUS_NOT_COLLECTED)

        # If not focused, focus on it
        if not self.name_entry_box.focused:
            self.name_entry_box._focused = True

    def on_key_press(self, symbol: int, modifiers: int):
        global HIGH_SCORES

        # Enter
        if symbol == arcade.key.ENTER:
            name = self.name_entry_box.text.strip()

            # Validate the name - min 1 char, max 15 chars
            if 1 <= len(name) <= 15:
                ENTER_SOUND.play(volume=NORMAL_VOLUME)

                # Append a new entry in the high scores file
                with open(HIGH_SCORES_FILE, mode="a") as high_scores_file:
                    high_scores_file.write(f"{name},{self.window.level_number},{self.window.score},"
                                           f"{time.asctime()}\n")

                # Remove the input box and reset the high scores list
                self.ui_manager.purge_ui_elements()
                HIGH_SCORES = get_high_scores()

                # If we have a new high score, play the high score voice
                high_score_view = HighScoreView(self.window, new_high_score=True) if \
                    self.window.score == HIGH_SCORES[0].score else HighScoreView(self.window)
                self.window.show_view(high_score_view)

            # Invalid name
            else:
                self.invalid_name_sound.play(volume=NORMAL_VOLUME)

        # Other characters
        else:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)


class HowToPlayView(arcade.View):
    """
    Explanation of how to play the game
    """

    def __init__(self, view: Union[PauseMenuView, MainMenuView]):
        """
        Initialize variables

        :param view: the view to return to, especially for Pause menu inside a level
        """
        super().__init__()
        self.view = view

        self.page = 0
        self.boundary = FullscreenBoundary()
        self.invalid_page_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/no_next_item_tone.wav")
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/how_to_play_music.mp3",
                                             streaming=True)

        self.center_x = SCREEN_WIDTH / 2
        self.line_width = 40  # Pixels from one line to another
        self.paragraph_width = 60  # Pixels from one paragraph to another

        # Sprite lists
        self.brick_list = arcade.SpriteList(is_static=True)
        self.icon_list_1 = arcade.SpriteList()
        self.icon_list_2 = arcade.SpriteList()

        # Append bricks
        section_spacing = 60  # Spacing between different sections of bricks
        brick_spacing = 30  # Spacing between bricks in the same section
        start_x = 200

        start_y = SCREEN_HEIGHT - 200
        for index, BrickType in enumerate([RED_, BLUE, GRN_, AQUA, GREY]):
            self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y))

        start_y -= brick_spacing
        for index, BrickType in enumerate([REDL, BLUL, GRNL, AQUL, GRYL]):
            self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y))

        start_y -= section_spacing
        for list_ in [[PINK, PNK1], [REDB, RDB1], [MUL4, MUL3, MUL2, MUL1]]:
            for index, BrickType in enumerate(list_):
                self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y - index * 10))
            start_y -= brick_spacing

        start_y -= section_spacing
        for index, BrickType in enumerate([UK__, BBB_, HAPY, RGRY, CUP_]):
            self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y))

        start_y -= brick_spacing
        for index, BrickType in enumerate([KNYA, FNM_, SAD_, LGRY]):
            self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y))

        start_y -= section_spacing
        self.brick_list.append(NWAL(center_x=start_x, center_y=start_y))

        start_y -= section_spacing
        self.brick_list.append(BLOK(center_x=start_x, center_y=start_y))

        start_y -= section_spacing
        for index, BrickType in enumerate([BONB, BONO, BONN, BONU, BONS]):
            self.brick_list.append(BrickType(center_x=start_x + index * 95, center_y=start_y - index * 10))

        # Append icons
        for index, IconType in enumerate([LENGTHEN, SHORTEN, SCORE, SHOOT, SPLIT, MAGNET]):
            self.icon_list_1.append(IconType(center_x=200, center_y=SCREEN_HEIGHT - 170 - index * 100))
        for index, IconType in enumerate([LIFE, SAFETY, ADVANCE, SPEED, SLOW, INVINCIBLE]):
            self.icon_list_2.append(IconType(center_x=200, center_y=SCREEN_HEIGHT - 170 - index * 100))

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        self.background_music.stop()
        WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def draw_page_0(self):
        """
        Draws the Instructions page
        """
        arcade.draw_text("Instructions", self.center_x, SCREEN_HEIGHT - 100, **MENU_TEXT_HEADING)
        arcade.draw_text("1. Break all the bricks to advance to the next level.\n    Bonus score of "
                         "100 is added for every life.\n\n2. Move the paddle using the left and right "
                         "arrow keys\n    to prevent the ball from falling. If the ball falls, you\n    "
                         "lose a life.\n\n3. Control the direction of the ball based on which side\n    "
                         "it lands on the paddle. If it lands on the left, it will\n    bounce to the left "
                         "and vice versa. Also, the ball\n    increases speed when it bounces farther away "
                         "from the\n    centre of the paddle.\n\n4. Collect icons that fall from the bricks "
                         "to give your\n    paddle special powers. However, if you lose a life,\n    your "
                         "paddle loses any special powers that it had.", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         **HOW_TO_PLAY_TEXT, width=1200)
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_1(self):
        """
        Draws the Bricks page
        """
        arcade.draw_text("Bricks", self.center_x, SCREEN_HEIGHT - 100, **MENU_TEXT_HEADING)
        self.brick_list.draw()

        arcade.draw_text("These are normal bricks. The top\nrow score 100 each, the rest 150.",
                         SCREEN_WIDTH - 500, SCREEN_HEIGHT - 215, **HOW_TO_PLAY_TEXT, width=750)
        arcade.draw_text("Some bricks need to be hit more than\nonce to destroy them. Each hit earns\nyou "
                         "200 points.", SCREEN_WIDTH - 550, SCREEN_HEIGHT - 330, **HOW_TO_PLAY_TEXT,
                         width=800)
        arcade.draw_text("The ones with the pretty pictures\nare worth 250 points each.",
                         SCREEN_WIDTH - 500, SCREEN_HEIGHT - 455, **HOW_TO_PLAY_TEXT, width=750)
        arcade.draw_text("This type only gives you 50 points per hit.", 710, SCREEN_HEIGHT - 530,
                         **HOW_TO_PLAY_TEXT)
        arcade.draw_text("No amount of battering can break this block.", 740, SCREEN_HEIGHT - 590,
                         **HOW_TO_PLAY_TEXT)
        arcade.draw_text("Collect these in the right order\nand earn 5,000 points! Otherwise,\nonly "
                         "2,000 extra.", SCREEN_WIDTH - 500, 180, **HOW_TO_PLAY_TEXT, width=750)

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_2(self):
        """
        Draws the first Icons page
        """
        arcade.draw_text("Icons", self.center_x, SCREEN_HEIGHT - 90, **MENU_TEXT_HEADING)

        self.icon_list_1.update_animation()
        self.icon_list_1.draw()
        arcade.draw_text("This icon increases the size of your paddle, allowing\nyou to reach balls "
                         "faster.\n\nIf you are unfortunate enough to catch this icon,\nyour paddle "
                         "will shrink in size.\n\nCollect this icon to get 5,000 bonus points added\nto "
                         "your score!\n\nThis icon allows you to complete a level faster by\nshooting the "
                         "bricks. Press SPACE to shoot.\n\nThis icon splits into 2 the next three "
                         "balls that hit\nyour paddle.\n\nIf you manage to capture this icon, your paddle "
                         "will\nbecome magnetic, allowing you to reposition the ball.\nPress SPACE to "
                         "release.", SCREEN_WIDTH / 2 + 50, SCREEN_HEIGHT / 2,
                         **HOW_TO_PLAY_TEXT, width=1100)

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_3(self):
        """
        Draws the second Icons page
        """
        arcade.draw_text("Icons", self.center_x, SCREEN_HEIGHT - 90, **MENU_TEXT_HEADING)

        self.icon_list_2.update_animation()
        self.icon_list_2.draw()
        arcade.draw_text("A very useful icon to catch. This adds you an extra\nlife in the game.\n\nThis "
                         "icon gives you a safety barrier that prevents\nthe ball from falling - but only "
                         "once.\n\nIf the current level is too tricky for you, catch this\nicon to advance "
                         "to the next level.\n\nAll the balls will speed up if you are unfortunate\nenough to "
                         "catch this icon.\n\nThis helpful icon slows down all the balls to a more\nmanageable "
                         "speed.\n\nThis cool icon makes the ball invincible for the next\n3 hits, allowing it "
                         "to pass straight through the\nbricks - but only breakable ones.",
                         SCREEN_WIDTH / 2 + 50, SCREEN_HEIGHT / 2, **HOW_TO_PLAY_TEXT, width=1100)

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def on_update(self, delta_time: float):
        # Loop the background music
        if self.background_music.get_stream_position() == 0:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        arcade.start_render()

        self.boundary.draw()  # Must be drawn first because of black background
        eval(f"self.draw_page_{self.page}()")

    def on_key_press(self, symbol: int, modifiers: int):
        # Right
        if symbol == arcade.key.RIGHT:
            # Check if there is a next page
            if hasattr(self, f"draw_page_{self.page + 1}"):
                self.page += 1
                SCROLL_SOUND.play(volume=NORMAL_VOLUME)

            # Next page doesn't exist
            else:
                self.invalid_page_sound.play(volume=NORMAL_VOLUME)

        # Left
        elif symbol == arcade.key.LEFT:
            # Check if there is a next page
            if hasattr(self, f"draw_page_{self.page - 1}"):
                self.page -= 1
                SCROLL_SOUND.play(volume=NORMAL_VOLUME)

            # Previous page doesn't exist
            else:
                self.invalid_page_sound.play(volume=NORMAL_VOLUME)

        # Enter or Escape
        elif symbol == arcade.key.ENTER or symbol == arcade.key.ESCAPE:
            self.window.show_view(self.view)


class PauseMenuView(arcade.View):
    def __init__(self, level: Level):
        super().__init__()
        self.level = level

        self.selected = 0
        self.options = ["Continue", "New Game", "How To Play", "Main Menu"]
        self.border = arcade.load_texture(f"{IMAGES_BASE_PATH}/boundaries/menu_boundary.png")
        self.background_music = arcade.Sound(f"{AUDIO_BASE_PATH}/background_music/pause_menu_music.mp3",
                                             streaming=True)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        self.background_music.stop()

    def on_update(self, delta_time: float):
        # Loop the background music
        if self.background_music.get_stream_position() == 0:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        # Level background
        self.level.on_draw()

        # Draws a dark filter on the level background
        arcade.draw_xywh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 100))

        # Draws the border and heading
        arcade.draw_scaled_texture_rectangle(self.level.boundary.center_x, self.level.boundary.center_y,
                                             self.border)
        arcade.draw_text("Paused", self.level.boundary.center_x, SCREEN_HEIGHT - 250,
                         **MENU_TEXT_HEADING)

        # Selection options
        for index, text in enumerate(self.options):
            if index == self.selected:
                style = MENU_TEXT_SELECTED
            else:
                style = MENU_TEXT_NORMAL

            arcade.draw_text(text, self.level.boundary.center_x, SCREEN_HEIGHT - 350 - index * 85,
                             **style)

    def on_key_press(self, symbol: int, modifiers: int):
        # Escape
        if symbol == arcade.key.ESCAPE:
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)
            self.window.show_view(self.level)

        # Down
        elif symbol == arcade.key.DOWN:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected += 1
            if self.selected >= len(self.options):
                self.selected = 0

        # Up
        elif symbol == arcade.key.UP:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected -= 1
            if self.selected < 0:
                self.selected = len(self.options) - 1

        # Enter
        elif symbol == arcade.key.ENTER:
            ENTER_SOUND.play(volume=NORMAL_VOLUME)

            # Continue game
            if self.selected == 0:
                self.window.show_view(self.level)

            # New game
            elif self.selected == 1:
                self.window.show_view(NewGameConfirmationView(self))

            # How to play
            elif self.selected == 2:
                self.window.show_view(HowToPlayView(self))

            # Main menu
            elif self.selected == 3:
                self.window.show_view(MainMenuConfirmationView(self))


class ConfirmationDialogueView(arcade.View, ABC):
    """
    Base class for confirmation dialogues
    """

    def __init__(self, action_text: str, view: arcade.View):
        """
        Initialize variables

        :param action_text: text form of what the player is trying to do
        :param view: view that we will return to if player chooses 'NO'
        """
        super().__init__()

        self.view = view
        self.selected = 1
        self.options = ["Yes", "No"]
        self.border = arcade.load_texture(f"{IMAGES_BASE_PATH}/boundaries/confirmation_dialogue_boundary.png")

        # If we are in a pause view
        if isinstance(self.view, PauseMenuView):
            self.center_x = self.view.level.boundary.center_x
            self.center_y = self.view.level.boundary.center_y

        # If we are in a main menu view
        else:
            self.center_x = SCREEN_WIDTH / 2
            self.center_y = SCREEN_HEIGHT / 2

        self.text1 = "Are you sure you want to"
        self.text2 = action_text + "?"
        self.text3 = "All progress will be lost!"

    @abstractmethod
    def yes_command(self):
        """
        Commands to execute when the player chooses 'YES'
        """
        pass

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        # Background
        self.view.on_draw()

        # Draws a dark filter on the view background
        arcade.draw_xywh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 100))

        arcade.draw_scaled_texture_rectangle(self.center_x, self.center_y, self.border)

        arcade.draw_text(self.text1, self.center_x, self.center_y + 90, **CONFIRMATION_DIALOGUE_TEXT)
        arcade.draw_text(self.text2, self.center_x, self.center_y + 50, **CONFIRMATION_DIALOGUE_TEXT)
        arcade.draw_text(self.text3, self.center_x, self.center_y - 10, **CONFIRMATION_DIALOGUE_TEXT)

        # Selection options
        for index, text in enumerate(self.options):
            if index == self.selected:
                style = MENU_TEXT_SELECTED
            else:
                style = MENU_TEXT_NORMAL

            arcade.draw_text(text, self.center_x - 150 + index * 300, self.center_y - 80, **style)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.RIGHT:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected += 1
            if self.selected >= len(self.options):
                self.selected = 0

        elif symbol == arcade.key.LEFT:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)
            self.selected -= 1
            if self.selected < 0:
                self.selected = len(self.options) - 1

        elif symbol == arcade.key.ENTER:
            ENTER_SOUND.play(volume=NORMAL_VOLUME)

            # Yes -> execute specific yes command
            if self.selected == 0:
                self.yes_command()

            # No -> return to the previous view
            else:
                self.window.show_view(self.view)

        # Esc -> return to the previous view
        elif symbol == arcade.key.ESCAPE:
            self.window.show_view(self.view)


class NewGameConfirmationView(ConfirmationDialogueView):
    """
    Confirms whether the player wants to start a new game
    """

    def __init__(self, view: arcade.View):
        super().__init__("start a new game", view)

    def yes_command(self):
        """
        Start a new game at level 1
        """
        self.view.window.reset_game()
        self.window.show_view(Level1(self.window))


class MainMenuConfirmationView(ConfirmationDialogueView):
    """
    Confirms whether the player wants to quit to main menu
    """

    def __init__(self, view: arcade.View):
        super().__init__("quit to main menu", view)

    def yes_command(self):
        """
        Go to main menu
        """
        self.window.show_view(MainMenuView(self.window))


class QuitGameConfirmationView(ConfirmationDialogueView):
    """
    Confirms whether the player wants to quit the game
    """

    def __init__(self, view: arcade.View):
        super().__init__("", view)

        # Override the text to display
        self.text1 = ""
        self.text2 = "Are you sure you want to"
        self.text3 = "quit the game?"

    def yes_command(self):
        """
        Quit the game
        """
        # Pause for a short while to hear the enter sound
        arcade.pause(0.2)
        self.window.close()
