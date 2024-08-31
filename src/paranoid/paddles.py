"""
The different types of paddles used in the game.

Created using MS Paint app
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Paddle" in `copy_properties_from` method
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade

from paranoid.balls import (
    Ball,
    InvinciBall,
    NormalBall,
)
from paranoid.constants import (
    AUDIO_BASE_PATH,
    IMAGES_BASE_PATH,
    PADDLE_SPEED,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Level


class Paddle(arcade.Sprite, ABC):
    """Base class for paddles."""

    def __init__(self, level: Level, **kwargs):
        """
        Create a paddle from an image.

        :param level: allows editing of level and window attributes
        """
        super().__init__(**kwargs)

        # Set the paddle texture
        self.initialize_texture()
        self.level = level

        self.center_x = self.level.boundary.center_x
        self.center_y = self.level.boundary.inner_bottom + 20
        self.paddle_speed = PADDLE_SPEED

        self.hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_paddle.wav")

        self.is_magnetic = False
        self.is_shooter_active = False
        self.invincible_balls = 0
        self.split_balls = 0

        self.magnetic_ball_list: list[Ball] = []

    @abstractmethod
    def initialize_texture(self):
        """Override in subclasses to set the paddle texture."""

    def on_update(self, delta_time: float = 1 / 60):
        """
        Paddle movement logic: (Distance = Speed x Time).

        :param delta_time: elapsed time since last update
        """
        # Only move the paddle if left or right is pressed, not both
        self.change_x = 0
        if self.level.left_pressed and not self.level.right_pressed:
            self.change_x = -self.paddle_speed
        elif self.level.right_pressed and not self.level.left_pressed:
            self.change_x = self.paddle_speed

        # Only update and check for collision with boundary if the paddle has velocity
        if self.change_x != 0:
            self.center_x += int(self.change_x * delta_time)
            self.collides_with_boundary()

    def collides_with_boundary(self):
        """Stop the paddle if it hits the boundary."""
        if self.right > self.level.boundary.inner_right:
            self.right = self.level.boundary.inner_right
        elif self.left < self.level.boundary.inner_left:
            self.left = self.level.boundary.inner_left

    def release_magnetic_balls(self):
        """Convert magnetic balls to non-magnetic balls which allows them to move."""
        for ball in self.magnetic_ball_list:
            new_ball = (
                ball.convert_to(InvinciBall)
                if ball.is_invincible
                else ball.convert_to(NormalBall)
            )
            new_ball.change_velocity()

            # If possible, splits the ball into two
            if self.split_balls > 0:
                new_ball.split_into_two()

        self.magnetic_ball_list.clear()

    def copy_properties_from(self, paddle: Paddle):
        """
        Copy properties from one paddle to another.

        :param paddle: the paddle from which the properties are copied
        """
        self.position = paddle.position
        self.is_magnetic = paddle.is_magnetic
        self.is_shooter_active = paddle.is_shooter_active
        self.invincible_balls = paddle.invincible_balls
        self.split_balls = paddle.split_balls
        self.magnetic_ball_list = paddle.magnetic_ball_list


class NormalPaddle(Paddle):
    """Normal paddle."""

    def initialize_texture(self):
        """Load the paddle texture."""
        self.texture = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/paddles/normal_paddle.png",
        )


class LongPaddle(Paddle):
    """Longer paddle."""

    def initialize_texture(self):
        """Load the paddle texture."""
        self.texture = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/paddles/long_paddle.png",
        )


class ShortPaddle(Paddle):
    """Shorter paddle."""

    def initialize_texture(self):
        """Load the paddle texture."""
        self.texture = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/paddles/short_paddle.png",
        )


class DemoPaddle(Paddle):
    """Base class for demo paddles."""

    def initialize_texture(self):
        """Load the paddle texture."""
        # Initializes the specific paddle based on the MRO of sub-class
        super().initialize_texture()

    def on_update(self, delta_time: float = 1 / 60):
        """Move the paddle similar to the ball."""
        self.center_x = self.level.ball_list[0].center_x
        self.collides_with_boundary()


class DemoNormalPaddle(DemoPaddle, NormalPaddle):
    """Demo version of the normal paddle."""


class DemoLongPaddle(DemoPaddle, LongPaddle):
    """Demo version of the long paddle."""


class DemoShortPaddle(DemoPaddle, ShortPaddle):
    """Demo version of the short paddle."""
