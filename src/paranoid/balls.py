"""
The different types of balls used in the game.

Created using MS Paint app
Image transparency of balls achieved using MS Powerpoint app
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Ball" in `convert_to` method
from __future__ import annotations

import math
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    TYPE_CHECKING,
    cast,
)

import arcade

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Boundary, Level

from paranoid.assets import Brick
from paranoid.constants import (
    BALL_MAX_SPEED,
    BALL_MIN_SPEED,
    DEBUGGING,
    IMAGES_BASE_PATH,
    NORMAL_VOLUME,
)


class Ball(arcade.Sprite, ABC):
    """Base class for all balls."""

    def __init__(
        self,
        boundary: Boundary,
        brick_list: arcade.SpriteList,
        level: Level = None,
        **kwargs,
    ):
        """
        Create a ball from an image.

        :param boundary: boundary which the ball will collide with
        :param brick_list: bricks which the ball will collide with
        :param level: allows editing of level and window attributes
        """
        super().__init__(**kwargs)

        self.is_invincible = (
            False  # Used to convert between magnetic and non-magnetic balls
        )

        # Sets the ball texture and possibly overrides is_invincible attribute
        self.initialize_texture()

        self.boundary = boundary
        self.brick_list = brick_list
        self.level = level

        self.center_x = self.boundary.center_x
        self.center_y = self.boundary.inner_bottom + 80

        self.velocity_angle = 45  # Angle at which ball travels across the screen
        self.ball_speed = BALL_MIN_SPEED  # Diagonal speed of the ball
        self.speed_increment = self.speed_decrement = 50
        self.set_velocity()

    @abstractmethod
    def initialize_texture(self):
        """Override in subclasses to set the ball texture."""

    def set_velocity(self):
        """Calculate the velocity of the ball from `ball_speed` and `velocity_angle`."""
        # Ensure the ball speed is within the limits
        # Fix black conflict with ruff (retain ruff formatting)
        # fmt: off
        self.ball_speed = (
            BALL_MAX_SPEED
            if self.ball_speed > BALL_MAX_SPEED
            else BALL_MIN_SPEED
            if self.ball_speed < BALL_MIN_SPEED
            else self.ball_speed
        )
        # fmt: on

        self.change_x = self.ball_speed * math.cos(math.radians(self.velocity_angle))
        self.change_y = self.ball_speed * math.sin(math.radians(self.velocity_angle))

    def change_velocity(self):
        """Change the ball velocity based on where it has hit the paddle."""
        # Get the x position where the ball has hit the paddle
        difference = self.center_x - self.level.paddle.left

        width = self.level.paddle.width
        middle = (
            20  # This is considered to be the width of the middle part of the paddle
        )
        lowest_angle = 25
        highest_angle = 70
        highest_speed = 40

        # Hits the left side
        if difference < width / 2 - middle / 2:
            angle = lowest_angle + difference
            angle = highest_angle if angle > highest_angle else angle

            self.velocity_angle = 180 - angle  # To make it bounce to the left
            self.ball_speed += highest_speed - difference

        # Hits the middle
        elif width / 2 - middle / 2 <= difference <= width / 2 + middle / 2:
            # If the ball is moving to the right, let it continue moving right
            if self.change_x > 0:
                self.velocity_angle = 55
            else:
                self.velocity_angle = 180 - 55
            self.ball_speed -= 20

        # Hits the right side
        else:
            angle = width - difference + lowest_angle

            self.velocity_angle = highest_angle if angle > highest_angle else angle
            self.ball_speed += difference - width + highest_speed

        self.set_velocity()

    def on_update(self, delta_time: float = 1 / 60):
        """
        Ball movement logic: (Distance = Speed x Time).

        :param delta_time: elapsed time since last update
        """
        # Update the x position of the ball and check for collisions
        self.center_x += int(self.change_x * delta_time)
        self.collides_with_boundary_moving_horizontally()
        self.collides_with_brick_moving_horizontally()
        self.collides_with_paddle_moving_horizontally()

        # Update the y position of the ball and check for collisions
        self.center_y += int(self.change_y * delta_time)
        self.collides_with_boundary_moving_vertically()
        self.collides_with_brick_moving_vertically()
        self.collides_with_paddle_moving_vertically()

    def collides_with_boundary_moving_horizontally(self):
        """Change the x direction of the ball if it collides with boundary."""
        # Right boundary
        if self.right > self.boundary.inner_right:
            self.right = self.boundary.inner_right
            self.change_x *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.side_hit_sound.play(volume=NORMAL_VOLUME, pan=1)

        # Left boundary
        elif self.left < self.boundary.inner_left:
            self.left = self.boundary.inner_left
            self.change_x *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.side_hit_sound.play(volume=NORMAL_VOLUME, pan=-1)

    def collides_with_boundary_moving_vertically(self):
        """Change the y direction of the ball if it collides with boundary."""
        # Top boundary
        if self.top > self.boundary.inner_top:
            self.top = self.boundary.inner_top
            self.change_y *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.top_hit_sound.play(volume=NORMAL_VOLUME)

        # Bottom boundary
        # Only bounce up if we are in debugging mode or in fullscreen mode
        elif (
            DEBUGGING or self.boundary.is_fullscreen
        ) and self.bottom < self.boundary.inner_bottom:
            self.bottom = self.boundary.inner_bottom
            self.change_y *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.bottom_hit_sound.play(volume=NORMAL_VOLUME)

        # If the ball goes below boundary, remove it from list
        elif self.top < self.boundary.inner_bottom:
            self.remove_from_sprite_lists()

    def collides_with_brick_moving_horizontally(self):
        """Change the x direction of the ball if it collides with brick."""
        hit_list = cast(list[Brick], self.collides_with_list(self.brick_list))

        # If the ball hits a brick, change its x direction only once
        if hit_list:
            brick = hit_list[0]

            # Prevents the ball from changing direction if it collides with safety barrier
            # moving horizontally (if safety barrier is created at the same instant that the
            # ball is going down - observed as a bug)
            if not brick.is_safety_barrier:
                # Check if ball hit the left or right side of brick
                if self.change_x > 0:
                    self.right = brick.left
                else:
                    self.left = brick.right

                # Change direction only once
                self.change_x *= -1

            # Only change the texture of the bricks if we are in a level
            if self.level is not None:
                for brick in hit_list:
                    brick.change_properties()

    def collides_with_brick_moving_vertically(self):
        """Change the y direction of the ball if it collides with brick."""
        hit_list = cast(list[Brick], self.collides_with_list(self.brick_list))

        # If the ball hits a brick, change its y direction only once
        if hit_list:
            brick = hit_list[0]

            # Check if ball hit the bottom or top side of brick
            if self.change_y > 0:
                self.top = brick.bottom
            else:
                self.bottom = brick.top

            # Change direction only once
            self.change_y *= -1

            # Only change the texture of the bricks if we are in a level
            if self.level is not None:
                for brick in hit_list:
                    brick.change_properties()

    def collides_with_paddle_moving_horizontally(self):
        """Change the x direction of the ball if it collides with paddle."""
        # Only check for collision with paddle if we are in a level
        if self.level is not None and self.collides_with_sprite(self.level.paddle):
            self.level.paddle.hit_sound.play(volume=NORMAL_VOLUME)

            # Check if ball hit the left or right side of paddle. This part
            # is a little tricky because both the ball and paddle can move

            # Ball is moving to the left and hits the left side of paddle
            # Checking "self.center_x < self.level.paddle.left" was found to have bugs
            if self.change_x < 0 and self.center_x < self.level.paddle.center_x:
                self.velocity_angle = 180 + 15
                self.ball_speed += 100
                self.set_velocity()

            # Ball is moving to the right and hits the right side of paddle
            elif self.change_x > 0 and self.center_x > self.level.paddle.center_x:
                self.velocity_angle = -15
                self.ball_speed += 100
                self.set_velocity()

            # Ball is moving to the right and hits the left side of paddle
            # No need to repeat checking the ball position
            elif self.change_x > 0:
                self.right = self.level.paddle.left
                self.change_x *= -1

            # Ball is moving to the left and hits right side of paddle
            elif self.change_x < 0:
                self.left = self.level.paddle.right
                self.change_x *= -1

    def collides_with_paddle_moving_vertically(self):
        """Change the y direction of the ball if it collides with paddle."""
        # Only check for collision with paddle if we are in a level
        if self.level is not None and self.collides_with_sprite(self.level.paddle):
            self.level.paddle.hit_sound.play(volume=NORMAL_VOLUME)

            # This part is also a little tricky because the ball could collide with
            # the side of the paddle while moving vertically

            # Ball is moving down and hits the left side of the paddle
            if (
                self.change_y < 0
                and self.center_y < self.level.paddle.top
                and self.center_x < self.level.paddle.left
            ):
                self.velocity_angle = 180 + 15
                self.ball_speed += 100
                self.set_velocity()

            # Ball is moving down and hits the right side of the paddle
            elif (
                self.change_y < 0
                and self.center_y < self.level.paddle.top
                and self.center_x > self.level.paddle.right
            ):
                self.velocity_angle = -15
                self.ball_speed += 100
                self.set_velocity()

            # If the ball hits the bottom of the paddle, change its direction
            elif self.change_y > 0:
                self.top = self.level.paddle.bottom
                self.change_y *= -1

            # If the ball hits the top side, change its properties
            elif self.change_y < 0:
                self.bottom = self.level.paddle.top
                self.change_properties()

    def change_properties(self):
        """If possible, change the ball's invincibility, magnetism, velocity and split it into two."""
        # Tries to create an invincible or a normal ball
        if self.level.paddle.invincible_balls > 0:
            ball = self.convert_to(InvinciBall) if not self.is_invincible else self
            self.level.paddle.invincible_balls -= 1
        else:
            ball = self.convert_to(NormalBall) if self.is_invincible else self

        # Makes the ball magnetic or bounces it normally
        if self.level.paddle.is_magnetic:
            magnetic_ball = (
                ball.convert_to(MagneticInvinciBall)
                if ball.is_invincible
                else ball.convert_to(MagneticNormalBall)
            )
            self.level.paddle.magnetic_ball_list.append(magnetic_ball)
        else:
            ball.change_velocity()

            # Splits the ball into two if possible
            if self.level.paddle.split_balls > 0:
                ball.split_into_two()

    def convert_to(self, BallType: type[Ball]) -> Ball:  # noqa: N803
        """
        Convert the ball from one type to another.

        :param ball_type: the type of ball that we are converting to
        :return: the ball that has been created
        """
        ball = BallType(self.boundary, self.brick_list, self.level)
        ball.position = self.position
        ball.change_horizontal_velocity()  # Doesn't affect magnetic balls

        self.level.ball_list.append(ball)
        self.remove_from_sprite_lists()

        return ball

    def split_into_two(self):
        """Create a new similar ball and launch it in the opposite x direction."""
        ball = self.__class__(self.level.boundary, self.brick_list, self.level)
        ball.position = self.position
        ball.velocity = [-self.change_x, self.change_y]

        self.level.ball_list.append(ball)
        self.level.paddle.split_balls -= 1

    def change_horizontal_velocity(self):
        """
        Prevent a newly-created ball from always being launched to the right side if it is on the middle part of the paddle.

        This is because when the ball is created, its change_x is always positive
        """
        if self.center_x < self.level.paddle.center_x:
            self.change_x = -1  # Make the change_x negative so that ball moves left

    def change_speed(self, action: str):
        """
        Increase or decrease the speed of the ball.

        :param action: 'increase' or 'decrease'
        """
        # Make a copy of the current velocity to allow ball to move in the same direction
        current_change_x = self.change_x
        current_change_y = self.change_y

        if action == "increase":
            self.ball_speed += self.speed_increment
        elif action == "decrease":
            self.ball_speed -= self.speed_decrement
        self.set_velocity()

        # Ensure the ball moves in the same direction as before
        if (current_change_x < 0 and self.change_x > 0) or (
            current_change_x > 0 and self.change_x < 0
        ):
            self.change_x *= -1
        if (current_change_y < 0 and self.change_y) > 0 or (
            current_change_y > 0 and self.change_y < 0
        ):
            self.change_y *= -1


class NormalBall(Ball):
    """Normal white ball."""

    def initialize_texture(self):
        """Load the ball texture."""
        self.texture = arcade.load_texture(f"{IMAGES_BASE_PATH}/balls/normal_ball.png")


class InvinciBall(Ball):
    """Ball that does not change direction when it hits a breakable brick."""

    def initialize_texture(self):
        """Load the ball texture."""
        self.texture = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/balls/invincible_ball.png",
        )
        self.is_invincible = True

    def collides_with_brick_moving_horizontally(self):
        """Change the x direction of the ball only if it collides with unbreakable brick."""
        hit_list = cast(list[Brick], self.collides_with_list(self.brick_list))

        # If the ball hits unbreakable brick, change its x direction only once
        for brick in hit_list:
            # If it hits safety barrier moving horizontally, don't change direction
            if not brick.is_breakable and not brick.is_safety_barrier:
                # Check if ball hit the left or right side of brick
                if self.change_x > 0:
                    self.right = brick.left
                else:
                    self.left = brick.right

                # Change direction for both cases
                self.change_x *= -1
                break

        # Only change the texture of the bricks if we are in a level
        if self.level is not None:
            for brick in hit_list:
                brick.change_properties()

    def collides_with_brick_moving_vertically(self):
        """Change the y direction of the ball only if it collides with unbreakable brick."""
        hit_list = cast(list[Brick], self.collides_with_list(self.brick_list))

        # If the ball hits an unbreakable brick or the safety barrier,
        # change its y direction only once
        for brick in hit_list:
            # If it hits safety barrier moving vertically, change its direction
            if not brick.is_breakable or brick.is_safety_barrier:
                # Check if ball hit the bottom or top side of brick
                if self.change_y > 0:
                    self.top = brick.bottom
                else:
                    self.bottom = brick.top

                # Change direction for both cases
                self.change_y *= -1
                break

        # Only change the texture of the bricks if we are in a level
        if self.level is not None:
            for brick in hit_list:
                brick.change_properties()


class MagneticNormalBall(NormalBall):
    """Magnetic version of the normal ball."""

    def on_update(self, delta_time: float = 1 / 60):
        """Move the ball horizontally with the paddle."""
        # This ball MUST update before the paddle to prevent weird motion when the paddle
        # hits the boundary (causes the ball to move in the opposite direction and hence ball
        # may overhang). Also, DO NOT replace the code block below with "self.change_x =
        # self.level.paddle.change_x" as this also causes the unintended motion.

        # Move the ball similar to the paddle
        self.change_x = 0
        if self.level.left_pressed and not self.level.right_pressed:
            self.change_x = -self.level.paddle.paddle_speed
        elif self.level.right_pressed and not self.level.left_pressed:
            self.change_x = self.level.paddle.paddle_speed

        # Prevent the ball from sliding across the paddle when paddle collides with boundary
        if (
            self.level.paddle.left == self.boundary.inner_left
            and self.level.left_pressed
            or self.level.paddle.right == self.boundary.inner_right
            and self.level.right_pressed
        ):
            self.change_x = 0

        # Only update if the paddle/ball has velocity
        if self.change_x != 0:
            self.center_x += int(self.change_x * delta_time)
            self.collides_with_boundary_moving_horizontally()


class MagneticInvinciBall(MagneticNormalBall):
    """Invincible version of magnetic normal ball."""

    def initialize_texture(self):
        """Load the ball texture."""
        self.texture = arcade.load_texture(
            f"{IMAGES_BASE_PATH}/balls/invincible_ball.png",
        )
        self.is_invincible = True
