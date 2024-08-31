"""
Defines assets required in the game such as balls, paddles, bricks and icons.

Assets created using MS Paint app. Image transparency of balls achieved using
MS Powerpoint app.

Images for flags downloaded from: https://www.countryflags.com/ and resized using MS Paint app
Colors obtained using color picker on the original game
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Boundary" in Ball __init__ method
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    cast,
)

import arcade

from paranoid.bricks import Brick
from paranoid.constants import (
    AUDIO_BASE_PATH,
    BULLET_SPEED,
    IMAGES_BASE_PATH,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Level


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                              EXTRAS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class SafetyBarrier(Brick, arcade.SpriteSolidColor):
    """Safety barrier to prevent the ball from falling."""

    def __init__(self, level: Level, **kwargs):
        """Initialize safety barrier properties."""
        super().__init__(
            level=level,
            width=1080,
            height=2,
            color=arcade.color.WHITE,
            **kwargs,
        )

        self.center_x = self.level.boundary.center_x
        self.center_y = self.level.boundary.inner_bottom + 7
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/hit_safety_barrier.wav",
        )
        self.is_safety_barrier = True

    def initialize_textures(self):
        """No textures to initialize."""


class Bullet(arcade.Sprite):
    """Bullet that can destroy bricks."""

    def __init__(self, level: Level, **kwargs):
        """Initialize bullet properties."""
        super().__init__(f"{IMAGES_BASE_PATH}/icons/bullet.png", scale=0.7, **kwargs)
        self.level = level

        self.center_x = self.level.paddle.center_x
        self.bottom = self.level.paddle.top
        self.change_y = BULLET_SPEED

    def on_update(self, delta_time: float = 1 / 60):
        """Move the bullet up and check for collisions with bricks."""
        self.center_y += int(self.change_y * delta_time)

        # Check for collision with bricks
        hit_list = cast(list[Brick], self.collides_with_list(self.level.brick_list))

        if hit_list:
            self.remove_from_sprite_lists()
            for brick in hit_list:
                brick.change_properties()

        # If it goes outside the playing field, remove it
        if self.bottom > self.level.boundary.inner_top:
            self.remove_from_sprite_lists()
