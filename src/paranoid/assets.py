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

from paranoid.constants import (
    AUDIO_BASE_PATH,
    BALL_MAX_SPEED,
    BALL_MIN_SPEED,
    BULLET_SPEED,
    DEBUGGING,
    ICON_SPEED,
    IMAGES_BASE_PATH,
    NORMAL_VOLUME,
    PADDLE_SPEED,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import (
        Boundary,
        Level,
    )


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             BALLS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                            PADDLES

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             BRICKS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Brick(arcade.Sprite, ABC):
    """Base class for all bricks."""

    def __init__(self, level: Level = None, **kwargs):
        """
        Initialize brick attributes.

        :param level: used to access level attributes
        """
        super().__init__(**kwargs)
        self.level = level

        self.is_breakable = True
        self.has_been_hit = (
            False  # Used to ensure a brick is not hit more than once in one go
        )
        self.is_safety_barrier = (
            False  # For collision detection btn safety barrier and invincible ball
        )

        self.score = 0
        self.letter = ""
        self.icon: Icon | None = None
        self.hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_brick.wav")

        self.images = []  # List of image files that will be converted to textures
        self.initialize_textures()  # Sub-classes possibly override other attributes,
        # hence must be last in __init__ call

    @abstractmethod
    def initialize_textures(self):
        """
        Override to populate the images list with the brick-image files.

        This parent method converts those images to textures and sets the initial texture
        """
        self.textures = [arcade.load_texture(image) for image in self.images]
        self.set_texture(self.cur_texture_index)

    def update(self):
        """
        Prevent a brick from being hit more than once in one go.

        This would change the texture more than once, increase the score more than once, etc.
        """
        # If the brick has been hit and is currently not being hit, allow it to be hit again
        if (
            self.has_been_hit
            and not self.collides_with_list(self.level.ball_list)
            and not self.collides_with_list(self.level.bullet_list)
        ):
            self.has_been_hit = False

    def change_properties(self):
        """Change brick and level properties after the brick has been hit."""
        # For breakable bricks, change texture or remove it
        if self.is_breakable and not self.has_been_hit:
            # Prevents the brick from being hit more than once in one go which would
            # increase the score twice, change the texture of a brick twice, etc.
            self.has_been_hit = True

            # Try setting the texture to the next texture in the list
            self.cur_texture_index += 1
            if self.cur_texture_index < len(self.textures):
                self.set_texture(self.cur_texture_index)
            else:
                self.remove_from_sprite_lists()

            # For either case, add the brick score and play hit sound
            self.level.window.score += self.score
            self.hit_sound.play(volume=NORMAL_VOLUME)

            # Add bonus letter if brick has a letter
            if self.letter:
                self.level.bonus_collection_order += self.letter

            # If the brick has an icon, deploy it only once
            if self.icon is not None:
                self.level.icon_list.append(self.icon)
                self.icon = None

        # For unbreakable bricks, play the hit sound
        elif not self.is_breakable:
            self.hit_sound.play(volume=NORMAL_VOLUME)


class RedBrick(Brick):
    """Normal red brick."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/red_brick.png"]
        super().initialize_textures()
        self.score = 100


class BlueBrick(Brick):
    """Normal blue brick."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/blue_brick.png"]
        super().initialize_textures()
        self.score = 100


class GreenBrick(Brick):
    """Normal green brick."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/green_brick.png"]
        super().initialize_textures()
        self.score = 100


class AquaBrick(Brick):
    """Normal aqua brick."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/aqua_brick.png"]
        super().initialize_textures()
        self.score = 100


class GreyBrick(Brick):
    """Normal grey brick."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/grey_brick.png"]
        super().initialize_textures()
        self.score = 100


class RedLineBrick(Brick):
    """Red brick with line."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/red_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class BlueLineBrick(Brick):
    """Blue brick with line."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/blue_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class GreenLineBrick(Brick):
    """Green brick with line."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/green_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class AquaLineBrick(Brick):
    """Aqua brick with line."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/aqua_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class GreyLineBrick(Brick):
    """Grey brick with line."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/grey_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class PinkBrick2(Brick):
    """Pink brick with 2 images."""

    def initialize_textures(self):
        """Load the brick images and score."""
        self.images = [
            f"{IMAGES_BASE_PATH}/bricks/pink_brick_1.png",
            f"{IMAGES_BASE_PATH}/bricks/pink_brick_2.png",
        ]

        # Shorten the image list for sub-classes
        if isinstance(self, PinkBrick1):
            self.images = self.images[1:]

        super().initialize_textures()
        self.score = 200


class PinkBrick1(PinkBrick2):
    """Pink brick with only 1 image."""


class RedBlueBrick2(Brick):
    """Red and blue brick with 2 images."""

    def initialize_textures(self):
        """Load the brick images and score."""
        self.images = [
            f"{IMAGES_BASE_PATH}/bricks/red_blue_brick_1.png",
            f"{IMAGES_BASE_PATH}/bricks/red_blue_brick_2.png",
        ]

        # Shorten the image list for sub-classes
        if isinstance(self, RedBlueBrick1):
            self.images = self.images[1:]

        super().initialize_textures()
        self.score = 200


class RedBlueBrick1(RedBlueBrick2):
    """Red and blue brick with only 1 image."""


class MultiColouredBrick4(Brick):
    """Multi-coloured brick with all 4 images."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [
            f"{IMAGES_BASE_PATH}/bricks/multi_coloured_brick_1.png",
            f"{IMAGES_BASE_PATH}/bricks/multi_coloured_brick_2.png",
            f"{IMAGES_BASE_PATH}/bricks/multi_coloured_brick_3.png",
            f"{IMAGES_BASE_PATH}/bricks/multi_coloured_brick_4.png",
        ]

        # Shorten the image list for sub-classes
        if isinstance(self, MultiColouredBrick3):
            self.images = self.images[1:]
        elif isinstance(self, MultiColouredBrick2):
            self.images = self.images[2:]
        elif isinstance(self, MultiColouredBrick1):
            self.images = self.images[3:]

        super().initialize_textures()
        self.score = 200


class MultiColouredBrick3(MultiColouredBrick4):
    """Multi-coloured brick with only 3 images."""


class MultiColouredBrick2(MultiColouredBrick4):
    """Multi-coloured brick with only 2 images."""


class MultiColouredBrick1(MultiColouredBrick4):
    """Multi-coloured brick with only 1 image."""


class UKFlagBrick(Brick):
    """Brick with UK flag."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/uk_flag_brick.png"]
        super().initialize_textures()
        self.score = 250


class KenyanFlagBrick(Brick):
    """Brick with Kenyan flag."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/kenyan_flag_brick.png"]
        super().initialize_textures()
        self.score = 250


class CupBrick(Brick):
    """Brick with cup image."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/cup_brick.png"]
        super().initialize_textures()
        self.score = 250


class BBBBrick(Brick):
    """Brick with BBB initials."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bbb_brick.png"]
        super().initialize_textures()
        self.score = 250


class FNMBrick(Brick):
    """Brick with FNM initials."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/fnm_brick.png"]
        super().initialize_textures()
        self.score = 250


class SmilingBrick(Brick):
    """Brick with smiling face."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/smiling_brick.png"]
        super().initialize_textures()
        self.score = 250


class FrowningBrick(Brick):
    """Brick with frowning face."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/frowning_brick.png"]
        super().initialize_textures()
        self.score = 250


class LeftPointingGreyBrick(Brick):
    """Grey brick with arrow pointing to the left."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/left_pointing_grey_brick.png"]
        super().initialize_textures()
        self.score = 250


class RightPointingGreyBrick(Brick):
    """Grey brick with arrow pointing to the right."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/right_pointing_grey_brick.png"]
        super().initialize_textures()
        self.score = 250


class NormalWallBrick(Brick):
    """Normal wall brick without right-side extension."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/normal_wall_brick.png"]
        super().initialize_textures()
        self.score = 50


class RightWallBrick(Brick):
    """Wall brick that is a bit larger and extends to the right to create seamless images."""

    def initialize_textures(self):
        """Load the brick image and score."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/right_wall_brick.png"]
        super().initialize_textures()
        self.score = 50


class UnbreakableBrick(Brick):
    """Brick that cannot be destroyed."""

    def initialize_textures(self):
        """Load the brick image and additional properties."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/unbreakable_brick.png"]
        super().initialize_textures()
        self.hit_sound = arcade.Sound(
            f"{AUDIO_BASE_PATH}/sounds/hit_unbreakable_brick.wav",
        )
        self.is_breakable = False


class BonusBrick(Brick, ABC):
    """Base class for bonus bricks."""

    def initialize_textures(self):
        """Load the brick sound and score."""
        super().initialize_textures()
        self.hit_sound = arcade.Sound(f"{AUDIO_BASE_PATH}/sounds/hit_bonus_brick.wav")
        self.score = 100


class BonusBBrick(BonusBrick):
    """Bonus brick with letter `B`."""

    def initialize_textures(self):
        """Load the brick image and letter."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bonus_b_brick.png"]
        super().initialize_textures()
        self.letter = "B"


class BonusOBrick(BonusBrick):
    """Bonus brick with letter `O`."""

    def initialize_textures(self):
        """Load the brick image and letter."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bonus_o_brick.png"]
        super().initialize_textures()
        self.letter = "O"


class BonusNBrick(BonusBrick):
    """Bonus brick with letter `N`."""

    def initialize_textures(self):
        """Load the brick image and letter."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bonus_n_brick.png"]
        super().initialize_textures()
        self.letter = "N"


class BonusUBrick(BonusBrick):
    """Bonus brick with letter `U`."""

    def initialize_textures(self):
        """Load the brick image and letter."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bonus_u_brick.png"]
        super().initialize_textures()
        self.letter = "U"


class BonusSBrick(BonusBrick):
    """Bonus brick with letter `S`."""

    def initialize_textures(self):
        """Load the brick image and letter."""
        self.images = [f"{IMAGES_BASE_PATH}/bricks/bonus_s_brick.png"]
        super().initialize_textures()
        self.letter = "S"


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                           SPECIAL BRICKS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class ParanoidIntroBrick(Brick):
    """Used in the game intro view."""

    def initialize_textures(self):
        """Load the brick image."""
        self.images = [f"{IMAGES_BASE_PATH}/boundaries/paranoid_intro_brick.png"]
        super().initialize_textures()


class MenuBrick(Brick):
    """Used in the pause and main menu views."""

    def initialize_textures(self):
        """Load the brick image."""
        self.images = [f"{IMAGES_BASE_PATH}/boundaries/menu_boundary.png"]
        super().initialize_textures()


class LeaderBoardBrick(Brick):
    """Used in the high-scores view."""

    def initialize_textures(self):
        """Load the brick image."""
        self.images = [f"{IMAGES_BASE_PATH}/boundaries/leader_board_brick.png"]
        super().initialize_textures()


class HighScoresBrick(Brick):
    """Used in the high-scores view."""

    def initialize_textures(self):
        """Load the brick image."""
        self.images = [f"{IMAGES_BASE_PATH}/boundaries/high_scores_brick.png"]
        super().initialize_textures()


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                               ICONS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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
