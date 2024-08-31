"""Different views used in the game."""

# Allows specifying of type checking hints without having to use string literals,
# e.g "GameIntroView" in BouncingIntroView __init__ method
from __future__ import annotations

import random
import time
from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade

# Prevent circular import error with levels.py https://stackoverflow.com/a/746067
import paranoid.levels
from paranoid.balls import NormalBall
from paranoid.boundaries import FullscreenBoundary
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
    CupBrick,
    FNMBrick,
    FrowningBrick,
    GreenBrick,
    GreenLineBrick,
    GreyBrick,
    GreyLineBrick,
    HighScoresBrick,
    KenyanFlagBrick,
    LeaderBoardBrick,
    LeftPointingGreyBrick,
    MenuBrick,
    MultiColouredBrick1,
    MultiColouredBrick2,
    MultiColouredBrick3,
    MultiColouredBrick4,
    NormalWallBrick,
    ParanoidIntroBrick,
    PinkBrick1,
    PinkBrick2,
    RedBlueBrick1,
    RedBlueBrick2,
    RedBrick,
    RedLineBrick,
    RightPointingGreyBrick,
    SmilingBrick,
    UKFlagBrick,
    UnbreakableBrick,
)
from paranoid.constants import (
    AUDIO_BASE_PATH,
    BGOTHL,
    BONUS_NOT_COLLECTED,
    CONFIRMATION_DIALOGUE_TEXT,
    DEMO_LEVEL_TIME,
    ENTER_NAME_HEADING,
    ENTER_SOUND,
    GRAVITY,
    HIGH_SCORES_FILE,
    HIGH_SCORES_HEADING,
    HIGH_SCORES_NAMES,
    HIGH_SCORES_NUMBERS,
    HOW_TO_PLAY_NEXT_BACK,
    HOW_TO_PLAY_TEXT,
    IMAGES_BASE_PATH,
    LEADER_BOARD_HEADING,
    LEVEL_INFO_TEXT,
    LOW_VOLUME,
    MAX_BOUNCES,
    MENU_TEXT_HEADING,
    MENU_TEXT_NORMAL,
    MENU_TEXT_SELECTED,
    NORMAL_VOLUME,
    PAUSE_TIME,
    RANDOM_BALLS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SCROLL_SOUND,
    TRANSITION_TIME,
    VELOCITY_RETAINED,
    WHOOSH_SOUND,
)
from paranoid.icons import (
    AdvanceLevelIcon,
    BonusLifeIcon,
    BonusScoreIcon,
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
from paranoid.utilities import get_high_scores

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    import pyglet.media

    from paranoid.main import ParanoidGame


class BouncingIntroView(arcade.View):
    """Introduce the game-intro and level views by bouncing several times."""

    def __init__(self, view: paranoid.levels.Level | GameIntroView):
        """Initialize view attributes."""
        super().__init__()

        self.view = view

        self.bottom = -SCREEN_HEIGHT
        self.change_y = 2
        self.bounce_count = 0
        self.elapsed_time = 0

        # Sounds
        self.bounce_sound_1 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/bounce_1.wav")
        self.bounce_sound_2 = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/bounce_2.wav")
        self.level_intro_whoosh_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/whoosh_2.wav",
        )

        # Only load the level intro voice in a level because in GameIntroView,
        # level number is 0
        if isinstance(self.view, paranoid.levels.Level):
            self.level_intro_voice = arcade.Sound(
                f"{AUDIO_BASE_PATH}/sounds/level_"
                f"{self.view.window.level_number}_voice.wav",
            )

        self.first_whoosh_sound_played = False
        self.second_whoosh_sound_played = False

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)

    def on_update(self, delta_time: float):
        """Bouncing logic."""
        self.elapsed_time += delta_time

        # Pause for a while before bouncing in a level view
        if (
            isinstance(self.view, GameIntroView)
            or isinstance(self.view, paranoid.levels.Level)
            and self.elapsed_time > PAUSE_TIME + TRANSITION_TIME * 2
        ):
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
        """Perform additional actions when in a level."""
        self.view.on_draw()

        # Only draw this when we are in a level
        if (
            isinstance(self.view, paranoid.levels.Level)
            and TRANSITION_TIME <= self.elapsed_time < PAUSE_TIME + TRANSITION_TIME
        ):
            arcade.draw_scaled_texture_rectangle(
                SCREEN_WIDTH / 2,
                -SCREEN_HEIGHT / 2,
                self.view.level_info_boundary,
            )
            arcade.draw_text(
                f"Level {self.view.window.level_number:02}",
                SCREEN_WIDTH / 2,
                -SCREEN_HEIGHT / 2,
                **LEVEL_INFO_TEXT,
            )

            # Play the first whoosh sound and voice as we start displaying the level info text
            if not self.first_whoosh_sound_played:
                self.level_intro_whoosh_sound.play(volume=NORMAL_VOLUME)
                self.level_intro_voice.play(volume=NORMAL_VOLUME)
                self.first_whoosh_sound_played = True

        # Play the second whoosh sound as we stop displaying level info text
        elif (
            isinstance(self.view, paranoid.levels.Level)
            and self.elapsed_time >= PAUSE_TIME + TRANSITION_TIME
        ):
            if not self.second_whoosh_sound_played:
                self.level_intro_whoosh_sound.play(volume=NORMAL_VOLUME)
                self.second_whoosh_sound_played = True


class LevelOutroView(arcade.View):
    """Exits a level by moving the screen up, then initiates a new level if one exists."""

    def __init__(self, level: paranoid.levels.Level):
        """Initialize attributes."""
        super().__init__()

        self.level = level
        self.bottom = 0
        self.change_y = 2
        self.level_up_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/level_up_sound.wav",
        )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)
        self.level_up_sound.play(volume=NORMAL_VOLUME)

    def on_update(self, delta_time: float):
        """Movement logic."""
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
        """Draw the level sprites."""
        self.level.on_draw()


class FullscreenView(arcade.View):
    """Base class for fullscreen views."""

    def __init__(self, window: ParanoidGame):
        """Initialize attributes."""
        super().__init__()
        self.window = window

        self.boundary = FullscreenBoundary()
        self.ball_list = arcade.SpriteList()
        self.brick_list = arcade.SpriteList(use_spatial_hash=True, is_static=True)
        self.sound_player: pyglet.media.Player | None = None

        # Override in sub-classes
        self.background_music: arcade.Sound | None = None

    def add_random_balls(self):
        """Add balls at random points, ensuring they are not place on top of a brick or another ball."""
        for i in range(RANDOM_BALLS):
            placed_successfully = False
            ball = NormalBall(self.boundary, self.brick_list)

            # Randomize ball velocity directions
            ball.velocity_angle = random.randrange(45, 60)
            ball.set_velocity()

            while not placed_successfully:
                ball.center_x = random.randrange(
                    self.boundary.inner_left + int(ball.width),
                    self.boundary.inner_right - int(ball.width),
                )
                ball.center_y = random.randrange(
                    self.boundary.inner_bottom + int(ball.height),
                    self.boundary.inner_top - int(ball.height),
                )

                if not ball.collides_with_list(
                    self.brick_list,
                ) and not ball.collides_with_list(self.ball_list):
                    placed_successfully = True

                    # Create random movement by setting some balls to move in opposite direction
                    if i % 2 == 0:
                        ball.change_x *= -1
                        ball.change_y *= -1

                    self.ball_list.append(ball)

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)
        self.sound_player = self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        """Run each time we exit from this view."""
        if self.sound_player is not None:
            self.background_music.stop(self.sound_player)

    def on_update(self, delta_time: float):
        """Update the balls' positions."""
        self.ball_list.on_update()

        # Loop the background music
        if (
            self.sound_player is not None
            and self.background_music.get_stream_position(self.sound_player) == 0
        ):
            self.sound_player = self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Draw all the sprites."""
        arcade.start_render()

        self.boundary.draw()
        self.brick_list.draw()
        self.ball_list.draw()


class GameIntroView(FullscreenView):
    """Starting screen of the game."""

    def __init__(self, window: ParanoidGame):
        """Initialize parameters."""
        super().__init__(window)

        self.first_time_showing = True
        self.brick_list.append(
            ParanoidIntroBrick(
                center_x=SCREEN_WIDTH / 2,
                center_y=SCREEN_HEIGHT / 2,
            ),
        )
        self.add_random_balls()

        self.elapsed_time = 0
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/game_intro_music.mp3",
            streaming=True,
        )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)

        if self.first_time_showing:
            self.first_time_showing = False
            self.window.show_view(BouncingIntroView(self))
        else:
            self.sound_player = self.background_music.play(volume=NORMAL_VOLUME)

    def on_update(self, delta_time: float):
        """Switch to the main menu view after some time."""
        super().on_update(delta_time)

        self.elapsed_time += delta_time
        if self.elapsed_time > PAUSE_TIME * 3:
            self.window.show_view(MainMenuView(self.window))

    def on_key_press(self, symbol: int, modifiers: int):
        """User can skip this view by pressing `ENTER` or `SPACE`."""
        # Fast-forward/skip
        if symbol == arcade.key.ENTER or symbol == arcade.key.SPACE:
            self.window.show_view(MainMenuView(self.window))


class MainMenuView(FullscreenView):
    """Main menu view."""

    def __init__(self, window: ParanoidGame):
        """Initialize attributes."""
        super().__init__(window)

        self.selected = 0
        self.elapsed_time = 0
        self.options = ["New Game", "How To Play", "High Scores", "Quit"]
        self.brick_list.append(
            MenuBrick(center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT / 2),
        )
        self.add_random_balls()
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/main_menu_music.mp3",
            streaming=True,
        )

    def on_update(self, delta_time: float):
        """Demo level logic."""
        super().on_update(delta_time)
        self.elapsed_time += delta_time

        # If we have paused for enough time, display a random demo level
        if self.elapsed_time > DEMO_LEVEL_TIME / 2:
            level_number = random.randrange(
                1,
                31,
            )  # Include level 30 TODO: Generalize this (not 30, 31, etc)
            level = eval(f"Level{level_number}(self.window, is_demo_level=True)")
            self.window.show_view(level)
            WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Draw the main menu text-options."""
        super().on_draw()

        # Draw main menu heading
        arcade.draw_text(
            "Main Menu",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 250,
            **MENU_TEXT_HEADING,
        )

        # Selection options
        for index, text in enumerate(self.options):
            style = MENU_TEXT_SELECTED if index == self.selected else MENU_TEXT_NORMAL

            arcade.draw_text(
                text,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT - 350 - index * 85,
                **style,
            )

    def on_key_press(self, symbol: int, modifiers: int):
        """Perform actions based on the key pressed."""
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
                self.window.show_view(paranoid.levels.Level1(self.window))

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
    """High-scores leaderboard view."""

    def __init__(self, window: ParanoidGame, new_high_score=False):
        """Initialize attributes."""
        super().__init__(window)
        self.new_high_score = new_high_score

        spacing = 60  # pixels

        # Create and position leader board brick
        self.leader_board_brick = LeaderBoardBrick(center_x=SCREEN_WIDTH / 2)
        self.leader_board_brick.top = self.boundary.inner_top - spacing
        self.brick_list.append(self.leader_board_brick)

        # Create and position high scores brick
        self.high_scores_brick = HighScoresBrick(center_x=SCREEN_WIDTH / 2)
        self.high_scores_brick.top = (
            self.boundary.inner_top - self.leader_board_brick.height - spacing * 2
        )
        self.brick_list.append(self.high_scores_brick)

        self.add_random_balls()
        self.new_high_score_voice = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/high_score_voice.wav",
        )
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/high_scores_music.mp3",
            streaming=True,
        )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=LOW_VOLUME)

        # If there is a new high score, play the high score voice
        if self.new_high_score:
            self.new_high_score_voice.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Show the high-scores."""
        super().on_draw()

        arcade.draw_text(
            "Leader Board",
            SCREEN_WIDTH / 2,
            self.leader_board_brick.center_y,
            **LEADER_BOARD_HEADING,
        )
        arcade.draw_text(
            "Name",
            self.high_scores_brick.left + 160,
            self.high_scores_brick.top - 40,
            **HIGH_SCORES_HEADING,
        )
        arcade.draw_text(
            "Level",
            self.high_scores_brick.right - 320,
            self.high_scores_brick.top - 40,
            **HIGH_SCORES_HEADING,
        )
        arcade.draw_text(
            "Score",
            self.high_scores_brick.right - 120,
            self.high_scores_brick.top - 40,
            **HIGH_SCORES_HEADING,
        )

        # Use index for positioning text
        for index, entry in enumerate(HIGH_SCORES):
            arcade.draw_text(
                f"{index + 1}",
                self.high_scores_brick.left + 60,
                self.high_scores_brick.top - 90 - 40 * index,
                **HIGH_SCORES_NUMBERS,
            )
            arcade.draw_text(
                entry.name,
                self.high_scores_brick.left + 110,
                self.high_scores_brick.top - 90 - 40 * index,
                **HIGH_SCORES_NAMES,
            )
            arcade.draw_text(
                entry.level,
                self.high_scores_brick.right - 300,
                self.high_scores_brick.top - 90 - 40 * index,
                **HIGH_SCORES_NUMBERS,
            )
            arcade.draw_text(
                f"{entry.score:,}",
                self.high_scores_brick.right - 60,
                self.high_scores_brick.top - 90 - 40 * index,
                **HIGH_SCORES_NUMBERS,
            )

    def on_key_press(self, symbol: int, modifiers: int):
        """Exit to main menu view by pressing `ENTER` or `ESCAPE`."""
        # Enter or Escape
        if symbol == arcade.key.ENTER or symbol == arcade.key.ESCAPE:
            self.window.show_view(MainMenuView(self.window))


class NameEntryView(arcade.View):
    """View for entering player's name if there is a new high score."""

    def __init__(self, window: ParanoidGame):
        """Initialize attributes."""
        super().__init__()
        self.window = window

        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        width = 450
        height = 50
        self.name_entry_box = arcade.gui.UIInputText(
            (SCREEN_WIDTH / 2) - (width / 2),
            (SCREEN_HEIGHT / 2 - (height / 2)),
            width=width,
            height=height,
        )
        self.name_entry_box.set_style_attrs(
            font_name=BGOTHL,
            font_size=30,
            font_color=arcade.color.WHITE,
            font_color_hover=arcade.color.WHITE,
            font_color_focus=arcade.color.WHITE,
            border_color=arcade.color.WHITE,
            border_color_hover=arcade.color.WHITE,
            border_color_focus=arcade.color.WHITE,
            bg_color_=arcade.color.BLACK,
            bg_color_hover=arcade.color.BLACK,
            bg_color_focus=arcade.color.BLACK,
            vmargin=10,
            margin_left=5,
        )
        self.name_entry_box._active = True  # Set it to always focus
        self.ui_manager.add(self.name_entry_box)

        self.border_list = arcade.SpriteList(is_static=True)
        self.border_list.append(
            arcade.Sprite(
                f"{IMAGES_BASE_PATH}/boundaries/confirmation_dialogue_boundary.png",
                center_x=SCREEN_WIDTH / 2,
                center_y=SCREEN_HEIGHT / 2,
            ),
        )
        self.invalid_name_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/invalid_name_tone.wav",
        )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)

    def on_hide_view(self):
        """Run each time we exit from this view."""
        WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Draw the input box and prompt text."""
        arcade.start_render()  # GUI elements are automatically drawn

        self.border_list.draw()
        arcade.draw_text(
            "Enter your name",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 80,
            **ENTER_NAME_HEADING,
        )
        arcade.draw_text(
            "Max: 15 characters",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 80,
            **BONUS_NOT_COLLECTED,
        )

        # If not focused, focus on it
        if not self.name_entry_box._active:
            self.name_entry_box._active = True

    def on_key_press(self, symbol: int, modifiers: int):
        """Save high scores to file based on user input."""
        global HIGH_SCORES

        # Enter
        if symbol == arcade.key.ENTER:
            name = self.name_entry_box.text.strip()

            # Validate the name - min 1 char, max 15 chars
            if 1 <= len(name) <= 15:
                ENTER_SOUND.play(volume=NORMAL_VOLUME)

                # Append a new entry in the high scores file
                with open(HIGH_SCORES_FILE, mode="a") as high_scores_file:
                    high_scores_file.write(
                        f"{name},{self.window.level_number},{self.window.score},"
                        f"{time.asctime()}\n",
                    )

                # Remove the input box and reset the high scores list
                self.ui_manager.clear()
                HIGH_SCORES = get_high_scores()

                # If we have a new high score, play the high score voice
                high_score_view = (
                    HighScoreView(self.window, new_high_score=True)
                    if self.window.score == HIGH_SCORES[0].score
                    else HighScoreView(self.window)
                )
                self.window.show_view(high_score_view)

            # Invalid name
            else:
                self.invalid_name_sound.play(volume=NORMAL_VOLUME)

        # Other characters
        else:
            SCROLL_SOUND.play(volume=NORMAL_VOLUME)


class HowToPlayView(arcade.View):
    """Explanation view for how to play the game."""

    def __init__(self, view: PauseMenuView | MainMenuView):
        """
        Initialize attributes.

        :param view: the view to return to, especially for Pause menu inside a `Level`
        """
        super().__init__()
        self.view = view

        self.page = 0
        self.boundary = FullscreenBoundary()
        self.invalid_page_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/no_next_item_tone.wav",
        )
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/how_to_play_music.mp3",
            streaming=True,
        )
        self.sound_player: pyglet.media.Player | None = None

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
        for index, BrickType in enumerate(  # noqa: N806
            [RedBrick, BlueBrick, GreenBrick, AquaBrick, GreyBrick],
        ):
            self.brick_list.append(
                BrickType(center_x=start_x + index * 95, center_y=start_y),
            )

        start_y -= brick_spacing
        for index, BrickType in enumerate(  # noqa: N806
            [RedLineBrick, BlueLineBrick, GreenLineBrick, AquaLineBrick, GreyLineBrick],
        ):
            self.brick_list.append(
                BrickType(center_x=start_x + index * 95, center_y=start_y),
            )

        start_y -= section_spacing
        for list_ in [
            [PinkBrick2, PinkBrick1],
            [RedBlueBrick2, RedBlueBrick1],
            [
                MultiColouredBrick4,
                MultiColouredBrick3,
                MultiColouredBrick2,
                MultiColouredBrick1,
            ],
        ]:
            for index, BrickType in enumerate(list_):  # noqa: N806
                self.brick_list.append(
                    BrickType(
                        center_x=start_x + index * 95,
                        center_y=start_y - index * 10,
                    ),
                )
            start_y -= brick_spacing

        start_y -= section_spacing
        for index, BrickType in enumerate(  # noqa: N806
            [UKFlagBrick, BBBBrick, SmilingBrick, RightPointingGreyBrick, CupBrick],
        ):
            self.brick_list.append(
                BrickType(center_x=start_x + index * 95, center_y=start_y),
            )

        start_y -= brick_spacing
        for index, BrickType in enumerate(  # noqa: N806
            [KenyanFlagBrick, FNMBrick, FrowningBrick, LeftPointingGreyBrick],
        ):
            self.brick_list.append(
                BrickType(center_x=start_x + index * 95, center_y=start_y),
            )

        start_y -= section_spacing
        self.brick_list.append(NormalWallBrick(center_x=start_x, center_y=start_y))

        start_y -= section_spacing
        self.brick_list.append(UnbreakableBrick(center_x=start_x, center_y=start_y))

        start_y -= section_spacing
        for index, BrickType in enumerate(  # noqa: N806
            [BonusBBrick, BonusOBrick, BonusNBrick, BonusUBrick, BonusSBrick],
        ):
            self.brick_list.append(
                BrickType(center_x=start_x + index * 95, center_y=start_y - index * 10),
            )

        # Append icons
        for index, IconType in enumerate(  # noqa: N806
            [
                LengthenPaddleIcon,
                ShortenPaddleIcon,
                BonusScoreIcon,
                ShootingIcon,
                SplitBallIcon,
                MagneticPaddleIcon,
            ],
        ):
            self.icon_list_1.append(
                IconType(center_x=200, center_y=SCREEN_HEIGHT - 170 - index * 100),
            )
        for index, IconType in enumerate(  # noqa: N806
            [
                BonusLifeIcon,
                SafetyBarrierIcon,
                AdvanceLevelIcon,
                SpeedUpBallsIcon,
                SlowDownBallsIcon,
                InvinciBallIcon,
            ],
        ):
            self.icon_list_2.append(
                IconType(center_x=200, center_y=SCREEN_HEIGHT - 170 - index * 100),
            )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)
        self.sound_player = self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        """Run each time we exit from this view."""
        self.background_music.stop(self.sound_player)
        WHOOSH_SOUND.play(volume=NORMAL_VOLUME)

    def draw_page_0(self):
        """Draw the Instructions page."""
        arcade.draw_text(
            "Instructions",
            self.center_x,
            SCREEN_HEIGHT - 100,
            **MENU_TEXT_HEADING,
        )
        arcade.draw_text(
            "1. Break all the bricks to advance to the next level.\n    Bonus score of "
            "100 is added for every life.\n\n2. Move the paddle using the left and right "
            "arrow keys\n    to prevent the ball from falling. If the ball falls, you\n    "
            "lose a life.\n\n3. Control the direction of the ball based on which side\n    "
            "it lands on the paddle. If it lands on the left, it will\n    bounce to the left "
            "and vice versa. Also, the ball\n    increases speed when it bounces farther away "
            "from the\n    centre of the paddle.\n\n4. Collect icons that fall from the bricks "
            "to give your\n    paddle special powers. However, if you lose a life,\n    your "
            "paddle loses any special powers that it had.",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            **HOW_TO_PLAY_TEXT,
            width=1200,
        )
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_1(self):
        """Draw the Bricks page."""
        arcade.draw_text(
            "Bricks",
            self.center_x,
            SCREEN_HEIGHT - 100,
            **MENU_TEXT_HEADING,
        )
        self.brick_list.draw()

        arcade.draw_text(
            "These are normal bricks. The top\nrow score 100 each, the rest 150.",
            SCREEN_WIDTH - 500,
            SCREEN_HEIGHT - 215,
            **HOW_TO_PLAY_TEXT,
            width=750,
        )
        arcade.draw_text(
            "Some bricks need to be hit more than\nonce to destroy them. Each hit earns\nyou "
            "200 points.",
            SCREEN_WIDTH - 550,
            SCREEN_HEIGHT - 330,
            **HOW_TO_PLAY_TEXT,
            width=800,
        )
        arcade.draw_text(
            "The ones with the pretty pictures\nare worth 250 points each.",
            SCREEN_WIDTH - 500,
            SCREEN_HEIGHT - 455,
            **HOW_TO_PLAY_TEXT,
            width=750,
        )
        arcade.draw_text(
            "This type only gives you 50 points per hit.",
            710,
            SCREEN_HEIGHT - 530,
            **HOW_TO_PLAY_TEXT,
        )
        arcade.draw_text(
            "No amount of battering can break this block.",
            740,
            SCREEN_HEIGHT - 590,
            **HOW_TO_PLAY_TEXT,
        )
        arcade.draw_text(
            "Collect these in the right order\nand earn 5,000 points! Otherwise,\nonly "
            "2,000 extra.",
            SCREEN_WIDTH - 500,
            180,
            **HOW_TO_PLAY_TEXT,
            width=750,
        )

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_2(self):
        """Draw the first Icons page."""
        arcade.draw_text(
            "Icons",
            self.center_x,
            SCREEN_HEIGHT - 90,
            **MENU_TEXT_HEADING,
        )

        self.icon_list_1.update_animation()
        self.icon_list_1.draw()
        arcade.draw_text(
            "This icon increases the size of your paddle, allowing\nyou to reach balls "
            "faster.\n\nIf you are unfortunate enough to catch this icon,\nyour paddle "
            "will shrink in size.\n\nCollect this icon to get 5,000 bonus points added\nto "
            "your score!\n\nThis icon allows you to complete a level faster by\nshooting the "
            "bricks. Press SPACE to shoot.\n\nThis icon splits into 2 the next three "
            "balls that hit\nyour paddle.\n\nIf you manage to capture this icon, your paddle "
            "will\nbecome magnetic, allowing you to reposition the ball.\nPress SPACE to "
            "release.",
            SCREEN_WIDTH / 2 + 50,
            SCREEN_HEIGHT / 2,
            **HOW_TO_PLAY_TEXT,
            width=1100,
        )

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)
        arcade.draw_text("Next>", SCREEN_WIDTH - 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def draw_page_3(self):
        """Draw the second Icons page."""
        arcade.draw_text(
            "Icons",
            self.center_x,
            SCREEN_HEIGHT - 90,
            **MENU_TEXT_HEADING,
        )

        self.icon_list_2.update_animation()
        self.icon_list_2.draw()
        arcade.draw_text(
            "A very useful icon to catch. This adds you an extra\nlife in the game.\n\nThis "
            "icon gives you a safety barrier that prevents\nthe ball from falling - but only "
            "once.\n\nIf the current level is too tricky for you, catch this\nicon to advance "
            "to the next level.\n\nAll the balls will speed up if you are unfortunate\nenough to "
            "catch this icon.\n\nThis helpful icon slows down all the balls to a more\nmanageable "
            "speed.\n\nThis cool icon makes the ball invincible for the next\n3 hits, allowing it "
            "to pass straight through the\nbricks - but only breakable ones.",
            SCREEN_WIDTH / 2 + 50,
            SCREEN_HEIGHT / 2,
            **HOW_TO_PLAY_TEXT,
            width=1100,
        )

        arcade.draw_text("<Back", 200, 100, **HOW_TO_PLAY_NEXT_BACK)

    def on_update(self, delta_time: float):
        """Loop the background music."""
        if self.background_music.get_stream_position(self.sound_player) == 0:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Draw the current page."""
        arcade.start_render()

        self.boundary.draw()  # Must be drawn first because of black background
        eval(f"self.draw_page_{self.page}()")

    def on_key_press(self, symbol: int, modifiers: int):
        """Navigate to next/previous page based on user input."""
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
    """Pause menu view inside a level."""

    def __init__(self, level: paranoid.levels.Level):
        """Initialize attributes."""
        super().__init__()
        self.level = level

        self.selected = 0
        self.options = ["Continue", "New Game", "How To Play", "Main Menu"]
        self.border = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/boundaries/menu_boundary.png",
        )
        self.background_music = arcade.Sound(
            f"{AUDIO_BASE_PATH}/background_music/pause_menu_music.mp3",
            streaming=True,
        )

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music.play(volume=NORMAL_VOLUME)

    def on_hide_view(self):
        """Run each time we exit from this view."""
        self.background_music.stop()

    def on_update(self, delta_time: float):
        """Loop the background music."""
        if self.background_music.get_stream_position() == 0:
            self.background_music.play(volume=NORMAL_VOLUME)

    def on_draw(self):
        """Draw the pause menu text-options."""
        # Level background
        self.level.on_draw()

        # Draws a dark filter on the level background
        arcade.draw_xywh_rectangle_filled(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            (0, 0, 0, 100),
        )

        # Draws the border and heading
        arcade.draw_scaled_texture_rectangle(
            self.level.boundary.center_x,
            self.level.boundary.center_y,
            self.border,
        )
        arcade.draw_text(
            "Paused",
            self.level.boundary.center_x,
            SCREEN_HEIGHT - 250,
            **MENU_TEXT_HEADING,
        )

        # Selection options
        for index, text in enumerate(self.options):
            style = MENU_TEXT_SELECTED if index == self.selected else MENU_TEXT_NORMAL

            arcade.draw_text(
                text,
                self.level.boundary.center_x,
                SCREEN_HEIGHT - 350 - index * 85,
                **style,
            )

    def on_key_press(self, symbol: int, modifiers: int):
        """Perform actions based on user input."""
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
    """Base class for confirmation dialogues."""

    def __init__(self, action_text: str, view: arcade.View):
        """
        Initialize attributes.

        :param action_text: text form of what the player is trying to do
        :param view: view that we will return to if player chooses 'NO'
        """
        super().__init__()

        self.view = view
        self.selected = 1
        self.options = ["Yes", "No"]
        self.border = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/boundaries/confirmation_dialogue_boundary.png",
        )

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
        """Command to execute when the player chooses `YES`."""

    def on_show(self):
        """Run each time we switch to this view."""
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        """Draw the confirmation menu text-options."""
        # Background
        self.view.on_draw()

        # Draws a dark filter on the view background
        arcade.draw_xywh_rectangle_filled(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            (0, 0, 0, 100),
        )

        arcade.draw_scaled_texture_rectangle(self.center_x, self.center_y, self.border)

        arcade.draw_text(
            self.text1,
            self.center_x,
            self.center_y + 90,
            **CONFIRMATION_DIALOGUE_TEXT,
        )
        arcade.draw_text(
            self.text2,
            self.center_x,
            self.center_y + 50,
            **CONFIRMATION_DIALOGUE_TEXT,
        )
        arcade.draw_text(
            self.text3,
            self.center_x,
            self.center_y - 10,
            **CONFIRMATION_DIALOGUE_TEXT,
        )

        # Selection options
        for index, text in enumerate(self.options):
            style = MENU_TEXT_SELECTED if index == self.selected else MENU_TEXT_NORMAL

            arcade.draw_text(
                text,
                self.center_x - 150 + index * 300,
                self.center_y - 80,
                **style,
            )

    def on_key_press(self, symbol: int, modifiers: int):
        """Perform actions based on user input."""
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
    """Confirms whether the player wants to start a new game."""

    def __init__(self, view: arcade.View):
        """Override `action_text`."""
        super().__init__("start a new game", view)

    def yes_command(self):
        """Reset all progress and start a new game at Level 1."""
        self.view.window.reset_game()
        self.window.show_view(paranoid.levels.Level1(self.window))


class MainMenuConfirmationView(ConfirmationDialogueView):
    """Confirms whether the player wants to quit to main menu."""

    def __init__(self, view: arcade.View):
        """Override `action_text`."""
        super().__init__("quit to main menu", view)

    def yes_command(self):
        """Go to main menu."""
        self.window.show_view(MainMenuView(self.window))


class QuitGameConfirmationView(ConfirmationDialogueView):
    """Confirms whether the player wants to quit the game."""

    def __init__(self, view: arcade.View):
        """Override text attributes."""
        super().__init__("", view)

        # Override the text to display
        self.text1 = ""
        self.text2 = "Are you sure you want to"
        self.text3 = "quit the game?"

    def yes_command(self):
        """Quit the game."""
        # Pause for a short while to hear the enter sound
        arcade.pause(0.2)
        self.window.close()
