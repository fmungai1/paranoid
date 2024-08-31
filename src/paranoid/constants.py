"""Constants used in all scripts."""

from pathlib import Path

import arcade

# I programmed this game specifically for the screen size I was working with
# at the time (1536 x 864 pixels) - fullscreen
# TODO: Add support for different screen sizes
SCREEN_WIDTH = 1536
SCREEN_HEIGHT = 864

# Debugging mode - prevents the ball from falling if True
DEBUGGING = False

# Speed constants
BALL_MIN_SPEED = 550
BALL_MAX_SPEED = BALL_MIN_SPEED + 300
PADDLE_SPEED = 500
ICON_SPEED = 100
BULLET_SPEED = 300

# Volumes
NORMAL_VOLUME = 0.3
LOW_VOLUME = 0.1

# Assets
ASSETS_BASE_PATH = Path(__file__).parent.parent.parent / "assets"
IMAGES_BASE_PATH = ASSETS_BASE_PATH / "images"
AUDIO_BASE_PATH = ASSETS_BASE_PATH / "audio"
FONTS_BASE_PATH = ASSETS_BASE_PATH / "fonts"
HIGH_SCORES_FILE = ASSETS_BASE_PATH / "high_scores.txt"

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

# Bouncing constants
MAX_BOUNCES = 3
GRAVITY = 0.4
VELOCITY_RETAINED = 0.7

# Global Sounds
ENTER_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/press_enter.wav")
SCROLL_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/scroll_options.wav")
WHOOSH_SOUND = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/whoosh_1.wav")

# Fonts
BGOTHL = "BankGothic Lt BT"
BGOTHM = "BankGothic Md BT"

# Text-styling dictionaries
DISPLAY_BLOCK_NUMBERS = {
    "color": (85, 255, 255),
    "font_size": 30,
    "font_name": BGOTHL,
    "anchor_x": "right",
}

DISPLAY_BLOCK_TEXT = {
    "color": (0, 0, 170),
    "font_size": 30,
    "font_name": BGOTHL,
    "width": 280,
    "align": "center",
    "anchor_x": "center",
    "anchor_y": "center",
}

DEMO_TEXT = {
    "color": (150, 150, 150),
    "font_size": 80,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

DISPLAY_BLOCK_TEXT_KEY = DISPLAY_BLOCK_TEXT.copy()
DISPLAY_BLOCK_TEXT_KEY.update(color=(170, 0, 0))

BONUS_NOT_COLLECTED = {
    "color": (170, 170, 170),
    "font_size": 30,
    "font_name": BGOTHL,
    "anchor_x": "center",
    "anchor_y": "center",
}

BONUS_COLLECTED = {
    "color": (85, 255, 85),
    "font_size": 35,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

LEVEL_INFO_TEXT = {
    "color": (215, 215, 215),
    "font_size": 40,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

MENU_TEXT_HEADING = {
    "color": (255, 85, 85),
    "font_size": 65,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

MENU_TEXT_NORMAL = {
    "color": (215, 215, 215),
    "font_size": 40,
    "font_name": BGOTHL,
    "anchor_x": "center",
    "anchor_y": "center",
}

MENU_TEXT_SELECTED = {
    "color": (85, 255, 255),
    "font_size": 50,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

ENTER_NAME_HEADING = MENU_TEXT_HEADING.copy()
ENTER_NAME_HEADING.update(font_size=50)

CONFIRMATION_DIALOGUE_TEXT = {
    "color": (215, 215, 215),
    "font_size": 30,
    "font_name": BGOTHL,
    "anchor_x": "center",
    "anchor_y": "center",
}

LEADER_BOARD_HEADING = {
    "color": (170, 0, 0),
    "font_size": 100,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

HIGH_SCORES_HEADING = {
    "color": (0, 0, 170),
    "font_size": 30,
    "font_name": BGOTHM,
    "anchor_x": "center",
    "anchor_y": "center",
}

HIGH_SCORES_NUMBERS = {
    "color": arcade.color.BLACK,
    "font_size": 20,
    "font_name": BGOTHL,
    "anchor_x": "right",
    "anchor_y": "center",
}

HIGH_SCORES_NAMES = {
    "color": arcade.color.BLACK,
    "font_size": 20,
    "font_name": BGOTHL,
    "anchor_x": "left",
    "anchor_y": "center",
}

HOW_TO_PLAY_TEXT = {
    "color": (85, 255, 85),
    "font_size": 30,
    "font_name": BGOTHL,
    "anchor_x": "center",
    "anchor_y": "center",
}

HOW_TO_PLAY_NEXT_BACK = MENU_TEXT_HEADING.copy()
HOW_TO_PLAY_NEXT_BACK.update(font_size=50)
