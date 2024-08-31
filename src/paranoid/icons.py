"""
The different types of icons used in the game.

Created using MS Paint app
Colors obtained using color picker on the original game
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Level" in Icon `__init__` method
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade

from paranoid.balls import (
    InvinciBall,
    MagneticInvinciBall,
    NormalBall,
)
from paranoid.constants import (
    AUDIO_BASE_PATH,
    ICON_SPEED,
    IMAGES_BASE_PATH,
    NORMAL_VOLUME,
)
from paranoid.extras import SafetyBarrier
from paranoid.paddles import (
    DemoLongPaddle,
    DemoNormalPaddle,
    DemoShortPaddle,
    LongPaddle,
    NormalPaddle,
    ShortPaddle,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Level


class Icon(arcade.Sprite, ABC):
    """Base class for all icons."""

    def __init__(self, level: Level = None, **kwargs):
        """
        Create an icon from a list of images.

        :param level: used to access level attributes. Level is `None` in How-to-play view
        """
        super().__init__(**kwargs)
        self.level = level

        self.frame_count = 0
        self.frames_per_update = 5
        self.change_y = -ICON_SPEED
        self.hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/collect_icon_tone.wav")

        self.images = []  # List of image files that will be converted to textures
        self.initialize_textures()  # Sub-classes possibly override other attributes,
        # hence must be last in __init__ call

    @abstractmethod
    def initialize_textures(self):
        """
        Override to populate the images list with the icon-image files.

        This parent method converts those images to textures and sets the initial texture
        """
        self.textures = [arcade.load_texture(image) for image in self.images]
        self.set_texture(self.cur_texture_index)

    @abstractmethod
    def activate_icon_property(self):
        """Override to execute what happens when an icon hits the paddle."""

    def update_animation(self, delta_time: float = 1 / 60):
        """Change the texture of the icon to create an animation."""
        self.frame_count += 1

        # Update the animation every x frames so that it is not too fast
        if self.frame_count % self.frames_per_update == 0:
            self.cur_texture_index += 1
            if self.cur_texture_index >= len(self.textures):
                self.cur_texture_index = 0
            self.set_texture(self.cur_texture_index)

    def on_update(self, delta_time: float = 1 / 60):
        """Update the icon's animation and move it."""
        self.update_animation()

        self.center_y += int(self.change_y * delta_time)

        # Check for collision with paddle
        if self.collides_with_sprite(self.level.paddle):
            self.activate_icon_property()
            self.hit_sound.play(volume=NORMAL_VOLUME)
            self.remove_from_sprite_lists()

        # Remove the icon if it goes below the playing field
        if self.top < self.level.boundary.inner_bottom:
            self.remove_from_sprite_lists()


class LengthenPaddleIcon(Icon):
    """Icon that increases the length of the paddle."""

    def initialize_textures(self):
        """Load the icon images and sound."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/lengthen_paddle_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/lengthen_paddle_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/lengthen_paddle_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/lengthen_paddle_icon_4.png",
        ]
        super().initialize_textures()
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/lengthen_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Increase the length of the paddle."""
        current_paddle = self.level.paddle

        # For demo level
        if self.level.is_demo_level:
            self.level.paddle = (
                DemoNormalPaddle(self.level)
                if isinstance(current_paddle, DemoShortPaddle)
                else DemoLongPaddle(self.level)
            )

        # Normal game play
        else:
            # If the current paddle is short, make it normal, else make it long
            self.level.paddle = (
                NormalPaddle(self.level)
                if isinstance(current_paddle, ShortPaddle)
                else LongPaddle(self.level)
            )
        self.level.paddle.copy_properties_from(current_paddle)
        self.level.paddle.collides_with_boundary()  # Reposition if the paddle collides with boundary

        # Increase the speed of the balls so that it's not too easy
        for ball in self.level.ball_list:
            ball.change_speed("increase")


class ShortenPaddleIcon(Icon):
    """Icon that decreases the length of the paddle."""

    def initialize_textures(self):
        """Load the icon images and sound."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/shorten_paddle_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/shorten_paddle_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/shorten_paddle_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/shorten_paddle_icon_4.png",
        ]
        super().initialize_textures()
        self.hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/shorten_icon_tone.wav")

    def activate_icon_property(self):
        """Decrease the length of the paddle."""
        current_paddle = self.level.paddle

        # For demo level
        if self.level.is_demo_level:
            self.level.paddle = (
                DemoNormalPaddle(self.level)
                if isinstance(current_paddle, DemoLongPaddle)
                else DemoShortPaddle(self.level)
            )

        # Normal game play
        else:
            # If the current paddle is long, make it normal, else make it short
            self.level.paddle = (
                NormalPaddle(self.level)
                if isinstance(current_paddle, LongPaddle)
                else ShortPaddle(self.level)
            )
        self.level.paddle.copy_properties_from(current_paddle)

        # If a ball is no longer on the paddle after it has shrunk, drop the ball
        for ball in self.level.paddle.magnetic_ball_list:
            if (
                ball.center_x < self.level.paddle.left
                or ball.center_x > self.level.paddle.right
            ):
                new_ball = (
                    ball.convert_to(InvinciBall)
                    if ball.is_invincible
                    else ball.convert_to(NormalBall)
                )
                new_ball.ball_speed = 200
                new_ball.velocity_angle = -90
                new_ball.set_velocity()
                self.level.paddle.magnetic_ball_list.remove(ball)


class MagneticPaddleIcon(Icon):
    """Icon that makes the paddle magnetic."""

    def initialize_textures(self):
        """Load the icon images."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/magnetic_paddle_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/magnetic_paddle_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/magnetic_paddle_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/magnetic_paddle_icon_4.png",
        ]
        super().initialize_textures()

    def activate_icon_property(self):
        """Make the paddle magnetic."""
        # Don't set magnetism in a demo level
        if not self.level.is_demo_level:
            self.level.paddle.is_magnetic = True


class BonusScoreIcon(Icon):
    """Icon that adds bonus score of 5000 points."""

    def __init__(self, level: Level = None, **kwargs):
        """Initialize adding-bonus sound."""
        super().__init__(level, **kwargs)
        self.adding_bonus_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/adding_bonus_3.wav",
        )

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/bonus_score_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/bonus_score_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/bonus_score_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Add a bonus score of 5000 points."""
        self.level.window.score += 5000
        self.adding_bonus_sound.play(volume=NORMAL_VOLUME)


class ShootingIcon(Icon):
    """Icon that gives the player ability to shoot the bricks."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/shooting_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/shooting_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/shooting_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Activate the paddle shooter."""
        self.level.paddle.is_shooter_active = True


class SplitBallIcon(Icon):
    """Icon that splits the next three balls into two."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/split_ball_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/split_ball_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/split_ball_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/split_ball_icon_4.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 10

    def activate_icon_property(self):
        """Increase the `split_balls` by 3."""
        self.level.paddle.split_balls += 3


class BonusLifeIcon(Icon):
    """Icon that adds an extra life."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/bonus_life_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/bonus_life_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/bonus_life_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Add an extra life."""
        self.level.window.lives += 1


class SafetyBarrierIcon(Icon):
    """Icon that activates the safety barrier."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_4.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_5.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_6.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_5.png",
            f"{IMAGES_BASE_PATH}/icons/safety_barrier_icon_4.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 3

    def activate_icon_property(self):
        """Activate the safety barrier."""
        self.level.brick_list.append(SafetyBarrier(self.level))


class AdvanceLevelIcon(Icon):
    """Icon that advances player to the next level."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/advance_level_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/advance_level_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/advance_level_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/advance_level_icon_4.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 3

    def activate_icon_property(self):
        """Advance to the next level."""
        # Don't advance level in a demo level
        if not self.level.is_demo_level:
            self.level.level_is_complete()


class SpeedUpBallsIcon(Icon):
    """Icon that increases the speed of all the balls."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/speed_up_ball_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/speed_up_ball_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/speed_up_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Increase the speed of all the balls and make the paddle non-magnetic."""
        self.level.paddle.is_magnetic = False
        self.level.paddle.release_magnetic_balls()

        for ball in self.level.ball_list:
            ball.change_speed("increase")


class SlowDownBallsIcon(Icon):
    """Icon that decreases the speed of all the balls."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/slow_down_ball_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/slow_down_ball_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/slow_down_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Decrease the speed of all the balls."""
        for ball in self.level.ball_list:
            ball.change_speed("decrease")


class InvinciBallIcon(Icon):
    """Icon that converts a normal ball to an invincible ball for three hits."""

    def initialize_textures(self):
        """Load the icon images and other properties."""
        self.images = [
            f"{IMAGES_BASE_PATH}/icons/invincible_ball_icon_1.png",
            f"{IMAGES_BASE_PATH}/icons/invincible_ball_icon_2.png",
            f"{IMAGES_BASE_PATH}/icons/invincible_ball_icon_3.png",
            f"{IMAGES_BASE_PATH}/icons/invincible_ball_icon_2.png",
        ]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/invincible_ball_icon_tone.wav",
        )

    def activate_icon_property(self):
        """Convert normal ball to invincible ball."""
        self.level.paddle.invincible_balls += 3

        # In case there are magnetic balls, change them to be invincible
        for ball in self.level.paddle.magnetic_ball_list:
            if not ball.is_invincible:
                new_ball = ball.convert_to(MagneticInvinciBall)
                self.level.paddle.magnetic_ball_list.append(new_ball)
                self.level.paddle.magnetic_ball_list.remove(ball)
                self.level.paddle.invincible_balls -= 1
