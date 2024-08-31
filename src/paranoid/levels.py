"""Contains boundaries, levels and views used in the game."""

# Allows specifying of type checking hints without having to use string literals,
# e.g "ParanoidGame" in Level __init__ method
from __future__ import annotations

import random
from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade
import arcade.gui

from paranoid.balls import (
    Ball,
    NormalBall,
)
from paranoid.boundaries import (
    DemoDisplayInfoBlock,
    DisplayInfoBlock,
    PlayingFieldBoundary,
)
from paranoid.bricks import (
    AquaBrick,
    AquaLineBrick,
    BBBBrick,
    BlueBrick,
    BlueLineBrick,
    BonusBBrick,
    BonusNBrick,
    BonusOBrick,
    BonusSBrick,
    BonusUBrick,
    Brick,
    CupBrick,
    FNMBrick,
    FrowningBrick,
    GreenBrick,
    GreenLineBrick,
    GreyBrick,
    GreyLineBrick,
    KenyanFlagBrick,
    LeftPointingGreyBrick,
    MultiColouredBrick1,
    MultiColouredBrick2,
    MultiColouredBrick3,
    MultiColouredBrick4,
    NormalWallBrick,
    PinkBrick1,
    PinkBrick2,
    RedBlueBrick1,
    RedBlueBrick2,
    RedBrick,
    RedLineBrick,
    RightPointingGreyBrick,
    RightWallBrick,
    SmilingBrick,
    UKFlagBrick,
    UnbreakableBrick,
)
from paranoid.constants import (
    AUDIO_BASE_PATH,
    BRICK_HEIGHT,
    BRICK_MARGIN,
    BRICK_WIDTH,
    DEMO_LEVEL_TIME,
    IMAGES_BASE_PATH,
    LEVEL_INFO_TEXT,
    LOW_VOLUME,
    NORMAL_VOLUME,
    PAUSE_TIME,
    TRANSITION_TIME,
    WHOOSH_SOUND,
)
from paranoid.extras import Bullet
from paranoid.icons import (
    AdvanceLevelIcon,
    BonusLifeIcon,
    BonusScoreIcon,
    Icon,
    InvinciBallIcon,
    LengthenPaddleIcon,
    MagneticPaddleIcon,
    SafetyBarrierIcon,
    ShootingIcon,
    ShortenPaddleIcon,
    SlowDownBallsIcon,
    SpeedUpBallsIcon,
    SplitBallIcon,
)
from paranoid.paddles import (
    DemoNormalPaddle,
    NormalPaddle,
)
from paranoid.utilities import get_high_scores
from paranoid.views import (
    BouncingIntroView,
    HighScoreView,
    LevelOutroView,
    MainMenuView,
    NameEntryView,
    PauseMenuView,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    import pyglet.media

    from paranoid.main import ParanoidGame


HIGH_SCORES = get_high_scores()


class Level(arcade.View, ABC):
    """Base class for all levels."""

    def __init__(self, window: ParanoidGame, is_demo_level=False):
        """Initialize level attributes."""
        super().__init__()
        self.window = window
        self.is_demo_level = is_demo_level

        # Sprite lists
        self.brick_list = arcade.SpriteList(
            use_spatial_hash=True,
        )  # Setting is_static causes bugs in multi-bricks
        self.breakable_brick_list = (
            arcade.SpriteList()
        )  # Only used to check if level is complete
        self.ball_list: list[Ball] | arcade.SpriteList = arcade.SpriteList()
        self.icon_list: list[Icon] | arcade.SpriteList = arcade.SpriteList()
        self.bullet_list: list[Bullet] | arcade.SpriteList = arcade.SpriteList()

        # Sprites and textures
        self.boundary = PlayingFieldBoundary()
        self.display_info = DisplayInfoBlock(level=self)
        self.level_info_boundary = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/boundaries/level_info_boundary.png",
        )
        self.paddle = NormalPaddle(level=self)
        self.ball_list.append(
            NormalBall(self.boundary, self.brick_list, level=self),
        )

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
        self.game_over_voice = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/game_over_voice.wav",
        )
        self.level_complete_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/level_complete_sound.wav",
        )
        self.level_complete_voice = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/level_complete_voice.wav",
        )
        self.adding_bonus_sound_1 = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/adding_bonus_1.wav",
        )
        self.adding_bonus_sound_2 = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/adding_bonus_2.wav",
        )
        self.adding_bonus_sound_3 = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/adding_bonus_3.wav",
        )
        self.shoot_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/shoot_bullet_sound.wav",
        )
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/level_{self.window.level_number}"
            f"_music.mp3",
            streaming=True,
        )
        self.sound_player: pyglet.media.Player | None = None

        # Overwrite certain attributes if we are in a demo level
        if self.is_demo_level:
            self.display_info = DemoDisplayInfoBlock()
            self.paddle = DemoNormalPaddle(self)
            self.game_is_active = True

        # Level setup stuff
        self.grid: list[list[type[Brick] | None]] = []
        self.icons: list[type[Icon]] = []
        self.populate_grid_and_icons()
        self.initialize_bricks_and_icons()

    @abstractmethod
    def populate_grid_and_icons(self):
        """
        Override to populate the grid with bricks in the desired positions.

        This is how the bricks will appear in each level. Also populate the list of icons
        that will appear in the level.

        .. code-block:: python

            self.grid = ...
            self.icons = ...
        """

    def initialize_bricks_and_icons(self):
        """
        Position the bricks on the correct x, y coordinates based on the grid.

        Also adds icons randomly to some of the bricks
        """
        # Each row is a list of brick classes that can be called to instantiate the brick
        for row_number, row in enumerate(self.grid):
            for column_number, BrickType in enumerate(row):  # noqa: N806
                # None refers to an empty cell
                if BrickType is not None:
                    center_y = (
                        self.boundary.inner_top
                        - BRICK_MARGIN
                        - BRICK_HEIGHT / 2
                        - (BRICK_MARGIN + BRICK_HEIGHT) * row_number
                    )

                    brick = BrickType(center_y=center_y, level=self)

                    # Switched from positioning using center_x to using left of the brick
                    # in order to create seamless images with wall bricks
                    brick.left = (
                        self.boundary.inner_left
                        + BRICK_MARGIN
                        + (BRICK_MARGIN + BRICK_WIDTH) * column_number
                    )

                    # Will be used to check if level is complete
                    if brick.is_breakable:
                        self.breakable_brick_list.append(brick)

                    self.brick_list.append(brick)

        random_bricks: list[Brick] = random.sample(
            list(self.breakable_brick_list),
            k=len(self.icons),
        )

        # Random icon assignment to the bricks
        for brick, IconType in zip(  # noqa: N806
            random_bricks,
            self.icons,
            strict=False,
        ):
            brick.icon = IconType(level=self)
            brick.icon.position = brick.position

    def level_is_complete(self):
        """Stop the background music and add bonus scores."""
        self.game_is_active = False
        self.level_complete = True
        self.elapsed_time = 0  # Reset the elapsed time
        self.background_music.stop(self.sound_player)

        # Set the bonus score
        if len(self.bonus_collection_order) == 5:  # All bonus letters collected
            if self.bonus_collection_order == "BONUS":
                self.bonus_score = 5000
            else:
                self.bonus_score = 2000

        self.bonus_score += self.window.lives * 100
        self.level_complete_sound.play(volume=NORMAL_VOLUME)

    def lose_a_life(self):
        """Reduce the lives by one and check whether the game is over."""
        self.game_is_active = False
        self.window.lives -= 1

        if self.window.lives == 0:
            self.game_over = True
        else:
            self.lost_a_life = True

        self.elapsed_time = 0  # Reset the elapsed time
        self.background_music.stop(self.sound_player)
        self.lost_a_life_sound.play(volume=NORMAL_VOLUME)

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)

        # For demo level, don't bounce
        if self.is_demo_level:
            self.sound_player = self.background_music.play(volume=LOW_VOLUME)

        # For normal level, bounce when showing the first time
        else:
            if self.first_time_showing:
                self.first_time_showing = False
                self.window.show_view(BouncingIntroView(self))
            else:
                self.sound_player = self.background_music.play(volume=LOW_VOLUME)

    def on_hide_view(self):
        """Run each time we exit from this view."""
        self.background_music.stop(self.sound_player)

    def on_update(self, delta_time: float):
        """Movement and game logic."""
        self.elapsed_time += delta_time

        # If we are in a demo level, display for some time then return to main menu
        if self.is_demo_level and self.elapsed_time > DEMO_LEVEL_TIME:
            self.window.show_view(MainMenuView(self.window))
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

        # Loop the background music
        # Background music stops if level is complete, lost a life or game over.
        # This prevents immediate restart of the background music.
        # Also prevents restart of music when exiting demo level.
        if (
            self.sound_player is not None
            and self.background_music.get_stream_position(self.sound_player) == 0
            and not self.lost_a_life
            and not self.game_over
            and not self.level_complete
            and not self.is_demo_level
        ):
            self.sound_player = self.background_music.play(volume=LOW_VOLUME)

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
            self.paddle = NormalPaddle(self)
            ball = NormalBall(self.boundary, self.brick_list, self)
            self.ball_list.append(ball)

            self.sound_player = self.background_music.play(volume=LOW_VOLUME)
            self.lost_a_life = False

        # Pause for a while before switching to the next view
        elif (
            self.game_over
            and self.elapsed_time > PAUSE_TIME * 2 + TRANSITION_TIME
            and self.window.display_score == self.window.score
        ):
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
        elif (
            self.level_complete
            and self.elapsed_time > PAUSE_TIME + TRANSITION_TIME
            and self.window.display_score == self.window.score
            and not self.load_next_level
        ):
            self.load_next_level = True
            self.elapsed_time_copy = self.elapsed_time  # Saves the current time

        # After the score has finished updating, wait for a while before
        # exiting the level
        elif (
            self.load_next_level
            and self.elapsed_time > self.elapsed_time_copy + PAUSE_TIME - 1
        ):
            self.window.show_view(LevelOutroView(self))

    def on_draw(self):
        """Draw all sprites in a level."""
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
            arcade.draw_scaled_texture_rectangle(
                self.boundary.center_x,
                self.boundary.center_y,
                self.level_info_boundary,
            )
            arcade.draw_text(
                "Game Over",
                self.boundary.center_x,
                self.boundary.center_y,
                **LEVEL_INFO_TEXT,
            )

            # Only play game over voice once
            if not self.game_over_voice_played:
                self.game_over_voice.play(volume=NORMAL_VOLUME)
                self.game_over_voice_played = True

        # Pause for a while before displaying the level complete message and adding bonus
        elif self.level_complete and self.elapsed_time > PAUSE_TIME:
            arcade.draw_scaled_texture_rectangle(
                self.boundary.center_x,
                self.boundary.center_y,
                self.level_info_boundary,
            )
            arcade.draw_text(
                "Level",
                self.boundary.center_x,
                self.boundary.center_y + 30,
                **LEVEL_INFO_TEXT,
            )
            arcade.draw_text(
                "Complete",
                self.boundary.center_x,
                self.boundary.center_y - 30,
                **LEVEL_INFO_TEXT,
            )

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
        """Process user key-press actions."""
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
            elif (
                symbol == arcade.key.SPACE
                and not self.lost_a_life
                and not self.game_over
                and not self.level_complete
            ):
                self.game_is_active = True
                if self.paddle.is_magnetic:
                    self.paddle.release_magnetic_balls()
                if self.paddle.is_shooter_active:
                    self.bullet_list.append(Bullet(self))
                    self.shoot_sound.play(volume=NORMAL_VOLUME)

            # Escape
            elif (
                symbol == arcade.key.ESCAPE
                and not self.game_over
                and not self.level_complete
            ):
                self.window.show_view(PauseMenuView(self))
                WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

                # Prevent paddle from moving after un-pausing if left or right key was pressed
                self.left_pressed = False
                self.right_pressed = False

    def on_key_release(self, _symbol: int, _modifiers: int):
        """Process user key-release actions."""
        if not self.is_demo_level:
            if _symbol == arcade.key.LEFT:
                self.left_pressed = False
            elif _symbol == arcade.key.RIGHT:
                self.right_pressed = False


# Shortened names for brick classes to be used in populating the grid (4 chars per brick)
RED_ = RedBrick
BLUE = BlueBrick
GRN_ = GreenBrick
AQUA = AquaBrick
GREY = GreyBrick
REDL = RedLineBrick
BLUL = BlueLineBrick
GRNL = GreenLineBrick
AQUL = AquaLineBrick
GRYL = GreyLineBrick
PNK2 = PinkBrick2
PNK1 = PinkBrick1
RDB2 = RedBlueBrick2
RDB1 = RedBlueBrick1
MUL4 = MultiColouredBrick4
MUL3 = MultiColouredBrick3
MUL2 = MultiColouredBrick2
MUL1 = MultiColouredBrick1
UK__ = UKFlagBrick
KNYA = KenyanFlagBrick
CUP_ = CupBrick
BBB_ = BBBBrick
FNM_ = FNMBrick
HAPY = SmilingBrick
SAD_ = FrowningBrick
LGRY = LeftPointingGreyBrick
RGRY = RightPointingGreyBrick
NWAL = NormalWallBrick
RWAL = RightWallBrick
BLOK = UnbreakableBrick
BONB = BonusBBrick
BONO = BonusOBrick
BONN = BonusNBrick
BONU = BonusUBrick
BONS = BonusSBrick

# Shortened names for icon classes to be used in populating the icons list
LENGTHEN = LengthenPaddleIcon
SHORTEN = ShortenPaddleIcon
MAGNET = MagneticPaddleIcon
SCORE = BonusScoreIcon
SHOOT = ShootingIcon
SPLIT = SplitBallIcon
LIFE = BonusLifeIcon
SAFETY = SafetyBarrierIcon
ADVANCE = AdvanceLevelIcon
SPEED = SpeedUpBallsIcon
SLOW = SlowDownBallsIcon
INVINCIBLE = InvinciBallIcon


class Level1(Level):
    """Level 1."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # Although it may be easier to use loops and list comprehensions, I decided to create
        # each grid manually for easier visualization of the levels

        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [AQUA, AQUA, AQUA, AQUA, AQUA, AQUA, PNK2, PNK2, AQUA, AQUA, AQUA, AQUA, AQUA, AQUA],
        ]
        # fmt: on

        self.icons = [MAGNET, SHORTEN, SAFETY, LENGTHEN, SPEED]


class Level2(Level):
    """Level 2."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, BLUL, None],
        ]
        # fmt: on

        self.icons = [SPEED, SPLIT, SPLIT, SHOOT, SLOW, SCORE, LIFE]


class Level3(Level):
    """Level 3."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, None, None, None, None, None, PNK2, PNK2, None, None, None, None, None, None],
        ]
        # fmt: on

        self.icons = [SHOOT, LIFE, INVINCIBLE, SCORE, LENGTHEN]


class Level4(Level):
    """Level 4."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
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
            [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
            [None, BLUL, REDL, None, None, None, AQUL, GRNL, None, None, None, REDL, BLUL, None],
            [None, BLUL, REDL, None, None, None, GRNL, AQUL, None, None, None, REDL, BLUL, None],
        ]
        # fmt: on

        self.icons = [SAFETY, SHORTEN, MAGNET, SPLIT, LENGTHEN, SHOOT, SCORE]


class Level5(Level):
    """Level 5."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [BLUE, BLUE, BLUE, BLUE, BLUE, None, None, None, None, BLUE, BLUE, BLUE, BLUE, BLUE],
            [BLUE, RED_, RED_, RED_, None, None, None, None, None, None, RED_, RED_, RED_, BLUE],
            [BLUE, GRN_, GRN_, None, None, None, None, None, None, None, None, GRN_, GRN_, BLUE],
            [BLUE, RED_, None, None, None, None, None, None, None, None, None, None, RED_, BLUE],
            [BLUE, None, None, None, None, None, MUL4, None, None, None, None, None, None, BLUE],
            [None, None, None, None, None, None, None, MUL4, None, None, None, None, None, None],
            [BLUE, None, None, None, None, None, None, None, None, None, None, None, None, BLUE],
            [BLUE, RED_, None, None, None, None, None, None, None, None, None, None, RED_, BLUE],
            [BLUE, GRN_, GRN_, None, None, None, None, None, None, None, None, GRN_, GRN_, BLUE],
            [BLUE, RED_, RED_, RED_, None, None, None, None, None, None, RED_, RED_, RED_, BLUE],
            [BLUE, BLUE, BLUE, BLUE, BLUE, None, None, None, None, BLUE, BLUE, BLUE, BLUE, BLUE],
        ]
        # fmt: on

        self.icons = [MAGNET, SCORE, MAGNET, SCORE, SHOOT, LIFE]


class Level6(Level):
    """Level 6."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, None, None, None, HAPY, None, PNK2, PNK2, None, HAPY, None, None, None, None],
            [None, None, None, None, None, HAPY, None, None, HAPY, None, None, None, None, None],
            [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None],
        ]
        # fmt: on

        self.icons = [SCORE, LIFE, SAFETY, SCORE, LENGTHEN]


class Level7(Level):
    """Level 7."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, GREY, None],
        ]
        # fmt: on

        self.icons = [SPEED, MAGNET, ADVANCE, SLOW, INVINCIBLE, SPLIT]


class Level8(Level):
    """Level 8."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, MUL2, MUL2, None, None, None, None, None, None],
            [None, None, None, None, None, None, RDB2, RDB2, None, None, None, None, None, None],
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
            [None, None, RGRY, RGRY, None, None, None, None, None, None, LGRY, LGRY, None, None],
        ]
        # fmt: on

        self.icons = [
            SAFETY,
            SHORTEN,
            SPLIT,
            LENGTHEN,
            LIFE,
            SPEED,
            SPLIT,
            SHORTEN,
            SCORE,
        ]


class Level9(Level):
    """Level 9."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, AQUA, AQUA, None, None, None, None, None, None, AQUA, AQUA, None, None],
            [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
            [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
            [None, None, GREY, RED_, RED_, AQUA, None, None, AQUA, RED_, RED_, GREY, None, None],
            [None, None, None, GREY, RED_, RED_, AQUA, AQUA, RED_, RED_, GREY, None, None, None],
            [None, None, None, None, GREY, RED_, RED_, RED_, RED_, GREY, None, None, None, None],
            [None, None, None, None, None, GREY, RED_, RED_, GREY, None, None, None, None, None],
            [None, None, None, None, None, None, RDB2, RDB2, None, None, None, None, None, None],
            [None, None, None, None, None, None, RDB2, RDB2, None, None, None, None, None, None],
            [None, None, None, None, None, None, RDB2, RDB2, None, None, None, None, None, None],
            [None, None, None, None, None, GREY, RED_, RED_, GREY, None, None, None, None, None],
            [None, None, None, None, GREY, RED_, RED_, RED_, RED_, GREY, None, None, None, None],
            [None, None, None, GREY, RED_, RED_, AQUA, AQUA, RED_, RED_, GREY, None, None, None],
            [None, None, GREY, RED_, RED_, AQUA, None, None, AQUA, RED_, RED_, GREY, None, None],
            [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
            [None, GREY, RED_, RED_, AQUA, None, None, None, None, AQUA, RED_, RED_, GREY, None],
            [None, None, AQUA, AQUA, None, None, None, None, None, None, AQUA, AQUA, None, None],
        ]
        # fmt: on

        self.icons = [
            LIFE,
            LENGTHEN,
            SHOOT,
            SPLIT,
            SPEED,
            SAFETY,
            SHOOT,
            LENGTHEN,
            SCORE,
            SLOW,
        ]


class Level10(Level):
    """Level 10."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, HAPY, HAPY, None, None, None, None, None, None],
            [None, None, None, None, None, HAPY, None, None, HAPY, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
            [None, RED_, None, RED_, None, RED_, None, None, RED_, None, RED_, None, RED_, None],
            [None, None, None, None, None, None, PNK2, UK__, None, None, None, None, None, None],
            [None, None, None, None, None, None, KNYA, PNK2, None, None, None, None, None, None],
            [BLUE, None, BLUE, None, BLUE, None, BLUE, BLUE, None, BLUE, None, BLUE, None, BLUE],
            [RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_, RED_],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, SAD_, None, None, SAD_, None, None, None, None, None],
            [None, None, None, None, None, None, SAD_, SAD_, None, None, None, None, None, None],
        ]
        # fmt: on

        self.icons = [INVINCIBLE, LENGTHEN, SCORE, SAFETY, SHORTEN, SPEED, SHOOT]


class Level11(Level):
    """Level 11."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, HAPY, SAD_, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [GREY, None, GREY, None, GREY, None, GREY, None, GREY, None, GREY, None, GREY, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [BLOK, PNK2, BLOK, PNK2, BLOK, PNK2, BLOK, PNK2, BLOK, PNK2, BLOK, PNK2, BLOK, PNK2],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, BLUL, BLOK, REDL, BLOK, BLUL, BLOK, REDL, BLOK, BLUL, BLOK, REDL, BLOK, BLUL],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
            [BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None, BLOK, None],
        ]
        # fmt: on

        self.icons = [LENGTHEN, MAGNET, SAFETY, SLOW, MAGNET, LENGTHEN, LIFE, LIFE]


class Level12(Level):
    """Level 12."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, RDB2, None, BONB, KNYA, None, RDB2, None, None, None, None],
            [AQUA, None, None, PNK2, None, None, UK__, BONO, None, None, PNK2, None, None, AQUA],
            [None, None, RDB2, None, None, None, BONN, KNYA, None, None, None, RDB2, None, None],
            [AQUA, None, None, PNK2, None, None, UK__, BONU, None, None, PNK2, None, None, AQUA],
            [None, None, None, None, RGRY, None, BONS, KNYA, None, LGRY, None, None, None, None],
            [AQUA, None, None, None, RGRY, None, None, None, None, LGRY, None, None, None, AQUA],
            [None, None, None, None, MUL4, RGRY, MUL4, MUL4, LGRY, MUL4, None, None, None, None],
            [AQUA, None, None, None, None, None, None, None, None, None, None, None, None, AQUA],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [BLUE, BLUE, None, None, None, None, None, None, None, None, None, None, BLUE, BLUE],
            [BLUE, BLUE, None, None, None, MUL2, None, None, MUL2, None, None, None, BLUE, BLUE],
        ]
        # fmt: on

        self.icons = [SLOW, SCORE, SPEED, SPLIT, LENGTHEN, LENGTHEN, LIFE]


class Level13(Level):
    """Level 13."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, GREY, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, RWAL, RWAL, RWAL, RWAL, NWAL, GRN_, GRN_, RWAL, RWAL, RWAL, RWAL, NWAL, None],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            SCORE,
            INVINCIBLE,
            SPLIT,
            LENGTHEN,
            SHORTEN,
            LENGTHEN,
            SHORTEN,
            LIFE,
            SPLIT,
            SPEED,
        ]


class Level14(Level):
    """Level 14."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, REDL, None],
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
            [None, None, None, RDB2, PNK2, None, None, REDL, None, None, None, None, None, None],
            [None, REDL, None, None, None, None, REDL, GRYL, REDL, None, None, None, None, None],
            [REDL, GREY, REDL, None, None, None, None, REDL, None, None, None, None, None, None],
            [None, REDL, None, None, HAPY, None, None, None, None, None, SAD_, None, None, None],
            [None, None, None, None, SAD_, HAPY, SAD_, None, None, None, SAD_, HAPY, SAD_, None],
            [None, None, None, None, None, HAPY, None, None, None, None, None, HAPY, None, None],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            SCORE,
            ADVANCE,
            LENGTHEN,
            INVINCIBLE,
            LIFE,
            SPEED,
            SPLIT,
        ]


class Level15(Level):
    """Level 15."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, AQUL, None, None, None, None, None, None, AQUL, None, None, None],
            [None, None, REDL, NWAL, REDL, None, None, None, None, REDL, NWAL, REDL, None, None],
            [None, BLUL, REDL, CUP_, REDL, AQUL, AQUL, AQUL, AQUL, REDL, CUP_, REDL, BLUL, None],
            [BLUL, NWAL, REDL, NWAL, REDL, None, CUP_, CUP_, None, REDL, NWAL, REDL, NWAL, BLUL],
            [BLUL, RWAL, NWAL, BLUL, None, NWAL, CUP_, CUP_, NWAL, None, BLUL, RWAL, NWAL, BLUL],
            [AQUL, RWAL, NWAL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, REDL, RWAL, NWAL, AQUL],
            [REDL, RWAL, NWAL, GRNL, None, NWAL, CUP_, CUP_, NWAL, None, GRNL, RWAL, NWAL, REDL],
            [REDL, NWAL, BLUL, NWAL, BLUL, None, CUP_, CUP_, None, BLUL, NWAL, BLUL, NWAL, REDL],
            [None, REDL, BLUL, CUP_, BLUL, GRNL, GRNL, GRNL, GRNL, BLUL, CUP_, BLUL, REDL, None],
            [None, None, BLUL, NWAL, BLUL, None, None, None, None, BLUL, NWAL, BLUL, None, None],
            [None, None, None, GRNL, None, None, None, None, None, None, GRNL, None, None, None],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            SHOOT,
            SPLIT,
            SAFETY,
            SHORTEN,
            LENGTHEN,
            INVINCIBLE,
            SCORE,
            MAGNET,
        ]


class Level16(Level):
    """Level 16."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, RWAL, NWAL, RED_, RED_, RWAL, NWAL, None, None, None, None],
            [None, UK__, UK__, UK__, RDB2, None, RDB2, RDB2, None, RDB2, KNYA, KNYA, KNYA, None],
            [RDB2, None, None, None, CUP_, CUP_, BBB_, FNM_, CUP_, CUP_, None, None, None, RDB2],
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
            [RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, RWAL, NWAL],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            SHOOT,
            SAFETY,
            MAGNET,
            ADVANCE,
            LIFE,
            SCORE,
            SHORTEN,
            SPEED,
            SLOW,
        ]


class Level17(Level):
    """Level 17."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [RGRY, GREY, None, None, CUP_, FNM_, None, None, BBB_, CUP_, None, None, GREY, LGRY],
        ]
        # fmt: on

        self.icons = [INVINCIBLE, SPEED, SCORE, SHOOT, SAFETY, LENGTHEN, MAGNET, SLOW]


class Level18(Level):
    """Level 18."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, None, None, None, None, BLOK, MUL4, MUL4, BLOK, None, None, None, None, None],
        ]
        # fmt: on

        self.icons = [
            SLOW,
            MAGNET,
            LIFE,
            LENGTHEN,
            SPEED,
            SPEED,
            SCORE,
            SAFETY,
            SAFETY,
            LIFE,
        ]


class Level19(Level):
    """Level 19."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [REDL, GRYL, None, None, None, None, None, None, None, None, None, None, GRYL, REDL],
            [None, REDL, BLUL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, BLUL, REDL, None],
            [None, None, REDL, BLUL, None, None, None, None, None, None, BLUL, REDL, None, None],
            [None, None, None, REDL, BLUL, None, None, None, None, BLUL, REDL, None, None, None],
            [None, None, None, None, REDL, PNK2, None, None, PNK2, REDL, None, None, None, None],
            [None, None, None, None, None, REDL, BLUL, BLUL, REDL, None, None, None, None, None],
            [None, None, None, None, None, GRYL, UK__, KNYA, GRYL, None, None, None, None, None],
            [None, None, None, None, None, GRYL, KNYA, UK__, GRYL, None, None, None, None, None],
            [None, None, None, None, None, REDL, BLUL, BLUL, REDL, None, None, None, None, None],
            [None, None, None, None, REDL, PNK2, None, None, PNK2, REDL, None, None, None, None],
            [None, None, None, REDL, BLUL, None, None, None, None, BLUL, REDL, None, None, None],
            [None, None, REDL, BLUL, None, None, None, None, None, None, BLUL, REDL, None, None],
            [None, REDL, BLUL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, GRNL, BLUL, REDL, None],
            [REDL, GRYL, None, None, None, None, None, None, None, None, None, None, GRYL, REDL],
        ]
        # fmt: on

        self.icons = [SPLIT, INVINCIBLE, ADVANCE, LIFE, SCORE, SHORTEN, SPEED, SLOW]


class Level20(Level):
    """Level 20."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [SAD_, SAD_, None, None, CUP_, None, None, None, None, CUP_, None, None, SAD_, SAD_],
            [SAD_, None, None, CUP_, CUP_, CUP_, None, None, CUP_, CUP_, CUP_, None, None, SAD_],
            [None, None, None, None, CUP_, None, None, None, None, CUP_, None, None, None, None],
            [None, None, None, None, None, MUL4, MUL4, MUL4, MUL4, None, None, None, None, None],
            [None, None, None, None, None, MUL4, PNK2, PNK2, MUL4, None, None, None, None, None],
            [None, None, BBB_, None, None, MUL4, RED_, RED_, MUL4, None, None, FNM_, None, None],
            [None, BBB_, RDB2, BBB_, None, MUL4, RED_, RED_, MUL4, None, FNM_, RDB2, FNM_, None],
            [None, BBB_, RDB2, BBB_, None, MUL4, RED_, RED_, MUL4, None, FNM_, RDB2, FNM_, None],
            [None, None, BBB_, None, None, MUL4, RED_, RED_, MUL4, None, None, FNM_, None, None],
            [None, None, None, None, None, MUL4, PNK2, PNK2, MUL4, None, None, None, None, None],
            [None, None, None, None, None, MUL4, MUL4, MUL4, MUL4, None, None, None, None, None],
            [None, None, None, None, CUP_, None, None, None, None, CUP_, None, None, None, None],
            [SAD_, None, None, CUP_, CUP_, CUP_, None, None, CUP_, CUP_, CUP_, None, None, SAD_],
            [SAD_, SAD_, None, None, CUP_, None, None, None, None, CUP_, None, None, SAD_, SAD_],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            INVINCIBLE,
            SPLIT,
            SHOOT,
            LENGTHEN,
            SHORTEN,
            MAGNET,
            SHOOT,
        ]


class Level21(Level):
    """Level 21."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [None, HAPY, None, None, None, None, HAPY, HAPY, None, None, None, None, HAPY, None],
            [None, SAD_, REDL, None, None, None, KNYA, REDL, None, None, None, REDL, SAD_, None],
            [None, None, KNYA, REDL, None, None, REDL, UK__, None, None, REDL, UK__, None, None],
            [None, None, None, REDL, REDL, None, KNYA, REDL, None, REDL, REDL, None, None, None],
            [None, None, None, None, KNYA, REDL, REDL, UK__, REDL, UK__, None, None, None, None],
            [None, None, None, None, None, REDL, None, None, REDL, None, None, None, None, None],
            [HAPY, REDL, KNYA, REDL, KNYA, None, PNK2, PNK2, None, UK__, REDL, UK__, REDL, HAPY],
            [SAD_, KNYA, REDL, KNYA, REDL, None, PNK2, PNK2, None, REDL, UK__, REDL, UK__, SAD_],
            [None, None, None, None, None, REDL, None, None, REDL, None, None, None, None, None],
            [None, None, None, None, KNYA, REDL, REDL, UK__, REDL, UK__, None, None, None, None],
            [None, None, None, REDL, REDL, None, KNYA, REDL, None, REDL, REDL, None, None, None],
            [None, None, KNYA, REDL, None, None, REDL, UK__, None, None, REDL, UK__, None, None],
            [None, HAPY, REDL, None, None, None, KNYA, REDL, None, None, None, REDL, HAPY, None],
            [None, SAD_, None, None, None, None, SAD_, SAD_, None, None, None, None, SAD_, None],
        ]
        # fmt: on

        self.icons = [
            LIFE,
            SHOOT,
            SPLIT,
            SLOW,
            INVINCIBLE,
            LENGTHEN,
            SPEED,
            SCORE,
            SHORTEN,
        ]


class Level22(Level):
    """Level 22."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [RDB2, None, None, RDB2, None, GRN_, None, None, GRN_, None, RDB2, None, None, RDB2],
            [RDB2, RDB2, RDB2, RDB2, None, GRN_, GRN_, GRN_, GRN_, None, RDB2, RDB2, RDB2, RDB2],
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
            [RDB2, RDB2, RDB2, RDB2, None, GRN_, GRN_, GRN_, GRN_, None, RDB2, RDB2, RDB2, RDB2],
            [RDB2, None, None, RDB2, None, GRN_, None, None, GRN_, None, RDB2, None, None, RDB2],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            LENGTHEN,
            SAFETY,
            SLOW,
            SPEED,
            ADVANCE,
            SCORE,
            SHORTEN,
            SHOOT,
        ]


class Level23(Level):
    """Level 23."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, MUL4, MUL4, None, None, None, None, None, None],
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
            [PNK2, None, GRN_, None, GRN_, None, PNK2, PNK2, None, GRN_, None, GRN_, None, PNK2],
        ]
        # fmt: on

        self.icons = [
            SHOOT,
            LENGTHEN,
            SCORE,
            SPLIT,
            INVINCIBLE,
            SPEED,
            SHORTEN,
            SHORTEN,
            LIFE,
        ]


class Level24(Level):
    """Level 24."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [RDB2, RDB2, None, None, None, None, PNK2, PNK2, None, None, None, None, RDB2, RDB2],
            [RDB2, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, RDB2],
            [None, None, None, None, AQUL, GRNL, REDL, REDL, GRNL, AQUL, None, None, None, None],
            [None, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, None],
            [None, None, None, PNK2, PNK2, None, PNK2, PNK2, None, PNK2, PNK2, None, None, None],
            [None, None, AQUL, None, REDL, RGRY, None, None, LGRY, REDL, None, AQUL, None, None],
            [None, AQUL, None, REDL, None, None, AQUL, AQUL, None, None, REDL, None, AQUL, None],
            [PNK2, PNK2, REDL, GRNL, REDL, AQUL, BLOK, BLOK, AQUL, REDL, GRNL, REDL, PNK2, PNK2],
            [None, AQUL, None, REDL, None, None, AQUL, AQUL, None, None, REDL, None, AQUL, None],
            [None, None, AQUL, None, REDL, RGRY, None, None, LGRY, REDL, None, AQUL, None, None],
            [None, None, None, PNK2, PNK2, None, PNK2, PNK2, None, PNK2, PNK2, None, None, None],
            [None, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, None],
            [None, None, None, None, AQUL, GRNL, REDL, REDL, GRNL, AQUL, None, None, None, None],
            [RDB2, None, None, None, None, AQUL, None, None, AQUL, None, None, None, None, RDB2],
            [RDB2, RDB2, None, None, None, None, PNK2, PNK2, None, None, None, None, RDB2, RDB2],
        ]
        # fmt: on

        self.icons = [
            INVINCIBLE,
            SHOOT,
            SAFETY,
            SCORE,
            SPEED,
            SLOW,
            LENGTHEN,
            SHOOT,
            SHORTEN,
            SPEED,
            MAGNET,
            LIFE,
        ]


class Level25(Level):
    """Level 25."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [REDL, PNK2, None, None, None, HAPY, None, None, HAPY, None, None, None, PNK2, REDL],
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
            [None, None, None, None, None, None, PNK2, PNK2, None, None, None, None, None, None],
            [None, None, None, None, None, None, PNK2, PNK2, None, None, None, None, None, None],
        ]
        # fmt: on

        self.icons = [
            LIFE,
            SPEED,
            LENGTHEN,
            INVINCIBLE,
            SPLIT,
            MAGNET,
            SCORE,
            SHORTEN,
            SLOW,
            ADVANCE,
        ]


class Level26(Level):
    """Level 26."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, None, None, None, None, GRN_, None, None, None, None, RED_, None, RED_, None],
        ]
        # fmt: on

        self.icons = [
            LENGTHEN,
            SHORTEN,
            SHORTEN,
            SPEED,
            SLOW,
            SCORE,
            SPLIT,
            SPEED,
            SAFETY,
        ]


class Level27(Level):
    """Level 27."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [RGRY, GRN_, RDB2, GRN_, RDB2, GRN_, RDB2, RDB2, GRN_, RDB2, GRN_, RDB2, GRN_, LGRY],
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            [RGRY, None, None, GRN_, PNK2, GRN_, PNK2, PNK2, GRN_, PNK2, GRN_, None, None, LGRY],
            [None, None, HAPY, None, None, None, None, None, None, None, None, HAPY, None, None],
            [RGRY, None, None, None, None, GRN_, RDB2, RDB2, GRN_, None, None, None, None, LGRY],
            [None, None, HAPY, None, CUP_, None, None, None, None, CUP_, None, HAPY, None, None],
            [BLOK, BLOK, BLOK, BLOK, BLOK, BLOK, MUL4, MUL4, BLOK, BLOK, BLOK, BLOK, BLOK, BLOK],
            [BLOK, BLOK, BLOK, BLOK, BLOK, BLOK, MUL4, MUL4, BLOK, BLOK, BLOK, BLOK, BLOK, BLOK],
        ]
        # fmt: on

        self.icons = [
            MAGNET,
            LIFE,
            SAFETY,
            LENGTHEN,
            MAGNET,
            LENGTHEN,
            SPEED,
            SHORTEN,
            SCORE,
            ADVANCE,
            SPLIT,
            SLOW,
            LIFE,
        ]


class Level28(Level):
    """Level 28."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, RGRY, None, None, None, MUL4, None, None, MUL4, None, None, None, LGRY, None],
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
            [RDB2, RDB2, RDB2, RDB2, RDB2, MUL4, None, None, MUL4, RDB2, RDB2, RDB2, RDB2, RDB2],
        ]
        # fmt: on

        self.icons = [
            SHOOT,
            INVINCIBLE,
            SCORE,
            SPLIT,
            SPEED,
            LIFE,
            SHOOT,
            SCORE,
            LENGTHEN,
            SHORTEN,
            SPEED,
            SHORTEN,
        ]


class Level29(Level):
    """Level 29."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None],
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
            [None, GRNL, REDL, REDL, GRNL, None, None, None, None, GRNL, REDL, REDL, GRNL, None],
        ]
        # fmt: on

        self.icons = [
            INVINCIBLE,
            SPEED,
            MAGNET,
            LENGTHEN,
            SPLIT,
            LIFE,
            SHORTEN,
            SCORE,
            SPLIT,
        ]


class Level30(Level):
    """Level 30."""

    def populate_grid_and_icons(self):
        """Add grid and icons for the level."""
        # fmt: off
        self.grid = [
            [REDL, None, None, None, None, None, REDL, REDL, None, None, None, None, None, REDL],
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
            [None, None, None, MUL4, MUL4, None, None, None, None, MUL4, MUL4, None, None, None],
        ]
        # fmt: on

        self.icons = [
            SHORTEN,
            LENGTHEN,
            SCORE,
            SCORE,
            SHOOT,
            SHOOT,
            SPEED,
            SAFETY,
            SHORTEN,
            INVINCIBLE,
            SPEED,
            LENGTHEN,
            SPEED,
            LIFE,
        ]
