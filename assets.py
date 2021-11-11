"""
Defines assets required in the game such as balls, paddles, bricks and icons

Assets created using MS Paint app. Image transparency of balls achieved using
MS Powerpoint app.

Images for flags downloaded from: https://www.countryflags.com/ and resized using MS Paint app
Colors obtained using color picker on the original game
"""
# Allows specifying of type checking hints without having to use string literals,
# e.g "Boundary" in Ball __init__ method
from __future__ import annotations

import arcade
import math

from abc import ABC, abstractmethod
from typing import List, Optional, cast, TYPE_CHECKING

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from levels import Boundary, Level

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


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             BALLS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Ball(arcade.Sprite, ABC):
    """
    Base class for all balls
    """

    def __init__(self,
                 boundary: Boundary,
                 brick_list: arcade.SpriteList,
                 level: Level = None,
                 **kwargs):
        """
        Creates a ball from an image

        :param boundary: boundary which the ball will collide with
        :param brick_list: bricks which the ball will collide with
        :param level: allows editing of level and window attributes
        """
        super().__init__(**kwargs)

        self.is_invincible = False  # Used to convert between magnetic and non-magnetic balls

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
        """
        Override in subclasses to set the ball texture
        """
        pass

    def set_velocity(self):
        """
        Calculates the velocity of the ball from ball_speed and velocity_angle
        """
        # Ensure the ball speed is within the limits
        self.ball_speed = BALL_MAX_SPEED if self.ball_speed > BALL_MAX_SPEED else BALL_MIN_SPEED if \
            self.ball_speed < BALL_MIN_SPEED else self.ball_speed

        self.change_x = self.ball_speed * math.cos(math.radians(self.velocity_angle))
        self.change_y = self.ball_speed * math.sin(math.radians(self.velocity_angle))

    def change_velocity(self):
        """
        Changes the ball velocity based on where it has hit the paddle
        """
        # Get the x position where the ball has hit the paddle
        difference = self.center_x - self.level.paddle.left

        width = self.level.paddle.width
        middle = 20  # This is considered to be the width of the middle part of the paddle
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
        Ball movement logic: (Distance = Speed x Time)

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
        """
        Changes the x direction of the ball if it collides with boundary
        """
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
        """
        Changes the y direction of the ball if it collides with boundary
        """
        # Top boundary
        if self.top > self.boundary.inner_top:
            self.top = self.boundary.inner_top
            self.change_y *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.top_hit_sound.play(volume=NORMAL_VOLUME)

        # Bottom boundary
        # Only bounce up if we are in debugging mode or in fullscreen mode
        elif (DEBUGGING or self.boundary.is_fullscreen) and self.bottom < self.boundary.inner_bottom:
            self.bottom = self.boundary.inner_bottom
            self.change_y *= -1

            # Only play sound when we are in a level
            if self.level is not None:
                self.boundary.bottom_hit_sound.play(volume=NORMAL_VOLUME)

        # If the ball goes below boundary, remove it from list
        elif self.top < self.boundary.inner_bottom:
            self.remove_from_sprite_lists()

    def collides_with_brick_moving_horizontally(self):
        """
        Changes the x direction of the ball if it collides with brick
        """
        hit_list = cast(List[Brick], self.collides_with_list(self.brick_list))

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
        """
        Changes the y direction of the ball if it collides with brick
        """
        hit_list = cast(List[Brick], self.collides_with_list(self.brick_list))

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
        """
        Changes the x direction of the ball if it collides with paddle
        """
        # Only check for collision with paddle if we are in a level
        if self.level is not None:
            if self.collides_with_sprite(self.level.paddle):
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
        """
        Changes the y direction of the ball if it collides with paddle
        """
        # Only check for collision with paddle if we are in a level
        if self.level is not None:
            if self.collides_with_sprite(self.level.paddle):
                self.level.paddle.hit_sound.play(volume=NORMAL_VOLUME)

                # This part is also a little tricky because the ball could collide with
                # the side of the paddle while moving vertically

                # Ball is moving down and hits the left side of the paddle
                if self.change_y < 0 and self.center_y < self.level.paddle.top and \
                        self.center_x < self.level.paddle.left:
                    self.velocity_angle = 180 + 15
                    self.ball_speed += 100
                    self.set_velocity()

                # Ball is moving down and hits the right side of the paddle
                elif self.change_y < 0 and self.center_y < self.level.paddle.top and \
                        self.center_x > self.level.paddle.right:
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
        """
        If possible, changes the ball's invincibility, magnetism, velocity and splits
        it into two
        """
        # Tries to create an invincible or a normal ball
        if self.level.paddle.invincible_balls > 0:
            ball = self.convert_to(InvinciBall) if not self.is_invincible else self
            self.level.paddle.invincible_balls -= 1
        else:
            ball = self.convert_to(NormalBall) if self.is_invincible else self

        # Makes the ball magnetic or bounces it normally
        if self.level.paddle.is_magnetic:
            magnetic_ball = ball.convert_to(MagneticInviciBall) if ball.is_invincible else \
                ball.convert_to(MagneticNormalBall)
            self.level.paddle.magnetic_ball_list.append(magnetic_ball)
        else:
            ball.change_velocity()

            # Splits the ball into two if possible
            if self.level.paddle.split_balls > 0:
                ball.split_into_two()

    def convert_to(self, ball_type: type) -> Ball:
        """
        Converts the ball from one type to another

        :param ball_type: the type of ball that we are converting to
        :return: the ball that has been created
        """
        ball = ball_type(self.boundary, self.brick_list, self.level)
        ball.position = self.position
        ball.change_horizontal_velocity()  # Doesn't affect magnetic balls

        self.level.ball_list.append(ball)
        self.remove_from_sprite_lists()

        return ball

    def split_into_two(self):
        """
        Creates a new similar ball and launches it in the opposite x direction
        """
        ball = self.__class__(self.level.boundary, self.brick_list, self.level)
        ball.position = self.position
        ball.velocity = [-self.change_x, self.change_y]

        self.level.ball_list.append(ball)
        self.level.paddle.split_balls -= 1

    def change_horizontal_velocity(self):
        """
        Prevents a newly-created ball from always being launched to the right side if
        it is on the middle part of the paddle. This is because when the ball is created,
        its change_x is always positive
        """
        if self.center_x < self.level.paddle.center_x:
            self.change_x = -1  # Make the change_x negative so that ball moves left

    def change_speed(self, action: str):
        """
        Increases or decreases the speed of the ball

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
        if (current_change_x < 0 and self.change_x > 0) or (current_change_x > 0 and self.change_x < 0):
            self.change_x *= -1
        if (current_change_y < 0 and self.change_y) > 0 or (current_change_y > 0 and self.change_y < 0):
            self.change_y *= -1


class NormalBall(Ball):
    """
    Normal white ball
    """

    def initialize_texture(self):
        self.texture = arcade.load_texture("images/balls/normal_ball.png")


class InvinciBall(Ball):
    """
    Ball that does not change direction when it hits a breakable brick
    """

    def initialize_texture(self):
        self.texture = arcade.load_texture("images/balls/invincible_ball.png")
        self.is_invincible = True

    def collides_with_brick_moving_horizontally(self):
        """
        Only changes the x direction of the ball if it collides with unbreakable brick
        """
        hit_list = cast(List[Brick], self.collides_with_list(self.brick_list))

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
        """
        Only changes the y direction of the ball if it collides with unbreakable brick
        """
        hit_list = cast(List[Brick], self.collides_with_list(self.brick_list))

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
    """
    Magnetic version of the normal ball
    """

    def on_update(self, delta_time: float = 1 / 60):
        """
        This ball only moves horizontally with the paddle
        """
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
        if self.level.paddle.left == self.boundary.inner_left and self.level.left_pressed or \
                self.level.paddle.right == self.boundary.inner_right and self.level.right_pressed:
            self.change_x = 0

        # Only update if the paddle/ball has velocity
        if self.change_x != 0:
            self.center_x += int(self.change_x * delta_time)
            self.collides_with_boundary_moving_horizontally()


class MagneticInviciBall(MagneticNormalBall):
    """
    Invincible version of magnetic normal ball
    """

    def initialize_texture(self):
        self.texture = arcade.load_texture("images/balls/invincible_ball.png")
        self.is_invincible = True


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                            PADDLES

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Paddle(arcade.Sprite, ABC):
    """
    Base class for paddles
    """

    def __init__(self, level: Level, **kwargs):
        """
        Creates a paddle from an image

        :param level: allows editing of level and window attributes
        """
        super().__init__(**kwargs)

        # Set the paddle texture
        self.initialize_texture()
        self.level = level

        self.center_x = self.level.boundary.center_x
        self.center_y = self.level.boundary.inner_bottom + 20
        self.paddle_speed = PADDLE_SPEED

        self.hit_sound = arcade.Sound("audio/sounds/hit_paddle.wav")

        self.is_magnetic = False
        self.activate_shooter = False
        self.invincible_balls = 0
        self.split_balls = 0

        self.magnetic_ball_list: List[Ball] = []

    @abstractmethod
    def initialize_texture(self):
        """
        Override in subclasses to set the ball texture
        """
        pass

    def on_update(self, delta_time: float = 1 / 60):
        """
        Paddle movement logic: (Distance = Speed x Time)

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
        """
        Stops the paddle if it hits the boundary
        """
        if self.right > self.level.boundary.inner_right:
            self.right = self.level.boundary.inner_right
        elif self.left < self.level.boundary.inner_left:
            self.left = self.level.boundary.inner_left

    def release_magnetic_balls(self):
        """
        Converts magnetic balls to non-magnetic balls which allows them to move
        """
        for ball in self.magnetic_ball_list:
            new_ball = ball.convert_to(InvinciBall) if ball.is_invincible else ball.convert_to(NormalBall)
            new_ball.change_velocity()

            # If possible, splits the ball into two
            if self.split_balls > 0:
                new_ball.split_into_two()

        self.magnetic_ball_list.clear()

    def copy_properties_from(self, paddle: Paddle):
        """
        Copies properties from one paddle to another

        :param paddle: the paddle from which the properties are copied
        """
        self.position = paddle.position
        self.is_magnetic = paddle.is_magnetic
        self.activate_shooter = paddle.activate_shooter
        self.invincible_balls = paddle.invincible_balls
        self.split_balls = paddle.split_balls
        self.magnetic_ball_list = paddle.magnetic_ball_list


class NormalPaddle(Paddle):
    def initialize_texture(self):
        self.texture = arcade.load_texture("images/paddles/normal_paddle.png")


class LongPaddle(Paddle):
    def initialize_texture(self):
        self.texture = arcade.load_texture("images/paddles/long_paddle.png")


class ShortPaddle(Paddle):
    def initialize_texture(self):
        self.texture = arcade.load_texture("images/paddles/short_paddle.png")


class DemoPaddle(Paddle):
    """
    Base class for demo paddles
    """

    def initialize_texture(self):
        # Initializes the specific paddle based on the MRO of sub-class
        super().initialize_texture()

    def on_update(self, delta_time: float = 1 / 60):
        """
        Moves the paddle similar to the ball
        """
        self.center_x = self.level.ball_list[0].center_x
        self.collides_with_boundary()


class DemoNormalPaddle(DemoPaddle, NormalPaddle):
    """
    Demo version of the normal paddle
    """
    pass


class DemoLongPaddle(DemoPaddle, LongPaddle):
    """
    Demo version of the long paddle
    """
    pass


class DemoShortPaddle(DemoPaddle, ShortPaddle):
    """
    Demo version of the short paddle
    """
    pass


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                             BRICKS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Brick(arcade.Sprite, ABC):
    """
    Base class for all bricks
    """

    def __init__(self, level: Level = None, **kwargs):
        """
        Initialize brick attributes

        :param level: used to access level attributes
        """
        super().__init__(**kwargs)
        self.level = level

        self.is_breakable = True
        self.has_been_hit = False  # Used to ensure a brick is not hit more than once in one go
        self.is_safety_barrier = False  # For collision detection btn safety barrier and invincible ball

        self.score = 0
        self.letter = ""
        self.icon: Optional[Icon] = None
        self.hit_sound = arcade.Sound("audio/sounds/hit_brick.wav")

        self.images = []  # List of image files that will be converted to textures
        self.initialize_textures()  # Sub-classes possibly override other attributes,
        # hence must be last in __init__ call

    @abstractmethod
    def initialize_textures(self):
        """
        Override to populate the images list with the icon-image files. This parent
        method converts those images to textures and sets the initial texture
        """
        self.textures = [arcade.load_texture(image) for image in self.images]
        self.set_texture(self.cur_texture_index)

    def update(self):
        """
        Prevents a brick from being hit more than once in one go. This would change the
        texture more than once, increase the score more than once, etc.
        """
        # If the brick has been hit and is currently not being hit, allow it to be hit again
        if self.has_been_hit and not self.collides_with_list(self.level.ball_list) and \
                not self.collides_with_list(self.level.bullet_list):
            self.has_been_hit = False

    def change_properties(self):
        """
        Changes brick and level properties after the brick has been hit
        """
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
            # self.ball_speed += 5
            # self.set_velocity()
            self.hit_sound.play(volume=NORMAL_VOLUME)


class RedBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/red_brick.png"]
        super().initialize_textures()
        self.score = 100


class BlueBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/blue_brick.png"]
        super().initialize_textures()
        self.score = 100


class GreenBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/green_brick.png"]
        super().initialize_textures()
        self.score = 100


class AquaBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/aqua_brick.png"]
        super().initialize_textures()
        self.score = 100


class GreyBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/grey_brick.png"]
        super().initialize_textures()
        self.score = 100


class RedLineBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/red_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class BlueLineBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/blue_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class GreenLineBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/green_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class AquaLineBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/aqua_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class GreyLineBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/grey_brick_with_line.png"]
        super().initialize_textures()
        self.score = 150


class PinkBrick2(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/pink_brick_1.png",
                       "images/bricks/pink_brick_2.png"]

        # Shorten the image list for sub-classes
        if isinstance(self, PinkBrick1):
            self.images = self.images[1:]

        super().initialize_textures()
        self.score = 200


class PinkBrick1(PinkBrick2):
    """
    A pink brick with only one image
    """
    pass


class RedBlueBrick2(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/red_blue_brick_1.png",
                       "images/bricks/red_blue_brick_2.png"]

        # Shorten the image list for sub-classes
        if isinstance(self, RedBlueBrick1):
            self.images = self.images[1:]

        super().initialize_textures()
        self.score = 200


class RedBlueBrick1(RedBlueBrick2):
    """
    A red blue brick with only one image
    """
    pass


class MultiColouredBrick4(Brick):
    """
    A multi-coloured brick with all 4 images
    """

    def initialize_textures(self):
        self.images = ["images/bricks/multi_coloured_brick_1.png",
                       "images/bricks/multi_coloured_brick_2.png",
                       "images/bricks/multi_coloured_brick_3.png",
                       "images/bricks/multi_coloured_brick_4.png"]

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
    """
    A multi-coloured brick with only 3 images
    """
    pass


class MultiColouredBrick2(MultiColouredBrick4):
    """
    A multi-coloured brick with only 2 images
    """
    pass


class MultiColouredBrick1(MultiColouredBrick4):
    """
    A multi-coloured brick with only 1 image
    """
    pass


class UKFlagBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/uk_flag_brick.png"]
        super().initialize_textures()
        self.score = 250


class KenyanFlagBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/kenyan_flag_brick.png"]
        super().initialize_textures()
        self.score = 250


class CupBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/cup_brick.png"]
        super().initialize_textures()
        self.score = 250


class BBBBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/bbb_brick.png"]
        super().initialize_textures()
        self.score = 250


class FNMBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/fnm_brick.png"]
        super().initialize_textures()
        self.score = 250


class SmilingBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/smiling_brick.png"]
        super().initialize_textures()
        self.score = 250


class FrowningBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/frowning_brick.png"]
        super().initialize_textures()
        self.score = 250


class LeftPointingGreyBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/left_pointing_grey_brick.png"]
        super().initialize_textures()
        self.score = 250


class RightPointingGreyBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/right_pointing_grey_brick.png"]
        super().initialize_textures()
        self.score = 250


class NormalWallBrick(Brick):
    """
    Normal wall brick without right-side extension
    """
    def initialize_textures(self):
        self.images = ["images/bricks/normal_wall_brick.png"]
        super().initialize_textures()
        self.score = 50


class RightWallBrick(Brick):
    """
    Wall brick that is a bit larger and extends to the right to create seamless images
    """
    def initialize_textures(self):
        self.images = ["images/bricks/right_wall_brick.png"]
        super().initialize_textures()
        self.score = 50


class UnbreakableBrick(Brick):
    def initialize_textures(self):
        self.images = ["images/bricks/unbreakable_brick.png"]
        super().initialize_textures()
        self.hit_sound = arcade.Sound("audio/sounds/hit_unbreakable_brick.wav")
        self.is_breakable = False


class BonusBrick(Brick):
    def initialize_textures(self):
        super().initialize_textures()
        self.hit_sound = arcade.Sound("audio/sounds/hit_bonus_brick.wav")
        self.score = 100


class BonusBBrick(BonusBrick):
    def initialize_textures(self):
        self.images = ["images/bricks/bonus_b_brick.png"]
        super().initialize_textures()
        self.letter = "B"


class BonusOBrick(BonusBrick):
    def initialize_textures(self):
        self.images = ["images/bricks/bonus_o_brick.png"]
        super().initialize_textures()
        self.letter = "O"


class BonusNBrick(BonusBrick):
    def initialize_textures(self):
        self.images = ["images/bricks/bonus_n_brick.png"]
        super().initialize_textures()
        self.letter = "N"


class BonusUBrick(BonusBrick):
    def initialize_textures(self):
        self.images = ["images/bricks/bonus_u_brick.png"]
        super().initialize_textures()
        self.letter = "U"


class BonusSBrick(BonusBrick):
    def initialize_textures(self):
        self.images = ["images/bricks/bonus_s_brick.png"]
        super().initialize_textures()
        self.letter = "S"


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                           SPECIAL BRICKS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class ParanoidIntroBrick(Brick):
    """
    Used in the game intro view
    """

    def initialize_textures(self):
        self.images = ["images/boundaries/paranoid_intro_brick.png"]
        super().initialize_textures()


class MenuBrick(Brick):
    """
    Used in the pause and main menu views
    """

    def initialize_textures(self):
        self.images = ["images/boundaries/menu_boundary.png"]
        super().initialize_textures()


class LeaderBoardBrick(Brick):
    """
    Used in the high scores view
    """

    def initialize_textures(self):
        self.images = ["images/boundaries/leader_board_brick.png"]
        super().initialize_textures()


class HighScoresBrick(Brick):
    """
    Used in the high scores view
    """

    def initialize_textures(self):
        self.images = ["images/boundaries/high_scores_brick.png"]
        super().initialize_textures()


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                               ICONS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Icon(arcade.Sprite, ABC):
    """
    Base class for all icons
    """

    def __init__(self, level: Level = None, **kwargs):
        """
        Creates an icon from a list of images

        :param level: used to access level attributes. Level is None in How-to-play view
        """
        super().__init__(**kwargs)
        self.level = level

        self.frame_count = 0
        self.frames_per_update = 5
        self.change_y = -ICON_SPEED
        self.hit_sound = arcade.Sound("audio/sounds/collect_icon_tone.wav")

        self.images = []  # List of image files that will be converted to textures
        self.initialize_textures()  # Sub-classes possibly override other attributes,
        # hence must be last in __init__ call

    @abstractmethod
    def initialize_textures(self):
        """
        Override to populate the images list with the icon-image files. This parent
        method converts those images to textures and sets the initial texture
        """
        self.textures = [arcade.load_texture(image) for image in self.images]
        self.set_texture(self.cur_texture_index)

    @abstractmethod
    def activate_icon_property(self):
        """
        Override to execute what happens when an icon hits the paddle
        """
        pass

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Changes the texture of the icon to create an animation
        """
        self.frame_count += 1

        # Update the animation every x frames so that it is not too fast
        if self.frame_count % self.frames_per_update == 0:
            self.cur_texture_index += 1
            if self.cur_texture_index >= len(self.textures):
                self.cur_texture_index = 0
            self.set_texture(self.cur_texture_index)

    def on_update(self, delta_time: float = 1 / 60):
        """
        Update the icon's animation and move it
        """
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
    """
    Increases the length of the paddle
    """

    def initialize_textures(self):
        self.images = ["images/icons/lengthen_paddle_icon_1.png",
                       "images/icons/lengthen_paddle_icon_2.png",
                       "images/icons/lengthen_paddle_icon_3.png",
                       "images/icons/lengthen_paddle_icon_4.png"]
        super().initialize_textures()
        self.hit_sound = arcade.Sound("audio/sounds/lengthen_icon_tone.wav")

    def activate_icon_property(self):
        current_paddle = self.level.paddle

        # For demo level
        if self.level.is_demo_level:
            self.level.paddle = DemoNormalPaddle(self.level) if isinstance(current_paddle, DemoShortPaddle) \
                else DemoLongPaddle(self.level)

        # Normal game play
        else:
            # If the current paddle is short, make it normal, else make it long
            self.level.paddle = NormalPaddle(self.level) if isinstance(current_paddle, ShortPaddle) \
                else LongPaddle(self.level)
        self.level.paddle.copy_properties_from(current_paddle)
        self.level.paddle.collides_with_boundary()  # Reposition if the paddle collides with boundary

        # Increase the speed of the balls so that it's not too easy
        for ball in self.level.ball_list:
            ball.change_speed("increase")


class ShortenPaddleIcon(Icon):
    """
    Decreases the length of the paddle
    """

    def initialize_textures(self):
        self.images = ["images/icons/shorten_paddle_icon_1.png",
                       "images/icons/shorten_paddle_icon_2.png",
                       "images/icons/shorten_paddle_icon_3.png",
                       "images/icons/shorten_paddle_icon_4.png"]
        super().initialize_textures()
        self.hit_sound = arcade.Sound("audio/sounds/shorten_icon_tone.wav")

    def activate_icon_property(self):
        current_paddle = self.level.paddle

        # For demo level
        if self.level.is_demo_level:
            self.level.paddle = DemoNormalPaddle(self.level) if isinstance(current_paddle, DemoLongPaddle) \
                else DemoShortPaddle(self.level)

        # Normal game play
        else:
            # If the current paddle is long, make it normal, else make it short
            self.level.paddle = NormalPaddle(self.level) if isinstance(current_paddle, LongPaddle) \
                else ShortPaddle(self.level)
        self.level.paddle.copy_properties_from(current_paddle)

        # If a ball is no longer on the paddle after it has shrunk, drop the ball
        for ball in self.level.paddle.magnetic_ball_list:
            if ball.center_x < self.level.paddle.left or ball.center_x > self.level.paddle.right:
                new_ball = ball.convert_to(InvinciBall) if ball.is_invincible else \
                    ball.convert_to(NormalBall)
                new_ball.ball_speed = 200
                new_ball.velocity_angle = -90
                new_ball.set_velocity()
                self.level.paddle.magnetic_ball_list.remove(ball)


class MagneticPaddleIcon(Icon):
    """
    Makes the paddle magnetic
    """

    def initialize_textures(self):
        self.images = ["images/icons/magnetic_paddle_icon_1.png",
                       "images/icons/magnetic_paddle_icon_2.png",
                       "images/icons/magnetic_paddle_icon_3.png",
                       "images/icons/magnetic_paddle_icon_4.png"]
        super().initialize_textures()

    def activate_icon_property(self):
        # Don't set magnetism in a demo level
        if not self.level.is_demo_level:
            self.level.paddle.is_magnetic = True


class BonusScoreIcon(Icon):
    """
    Adds bonus score of 5000 points
    """

    def __init__(self, level: Level = None, **kwargs):
        super().__init__(level, **kwargs)
        self.adding_bonus_sound = arcade.Sound("audio/sounds/adding_bonus_3.wav")

    def initialize_textures(self):
        self.images = ["images/icons/bonus_score_icon_1.png",
                       "images/icons/bonus_score_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound("audio/sounds/bonus_score_icon_tone.wav")

    def activate_icon_property(self):
        self.level.window.score += 5000
        self.adding_bonus_sound.play(volume=NORMAL_VOLUME)


class ShootingIcon(Icon):
    """
    Gives the player ability to shoot the bricks
    """

    def initialize_textures(self):
        self.images = ["images/icons/shooting_icon_1.png",
                       "images/icons/shooting_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound("audio/sounds/shooting_icon_tone.wav")

    def activate_icon_property(self):
        self.level.paddle.activate_shooter = True


class SplitBallIcon(Icon):
    """
    Splits the next three balls into two
    """

    def initialize_textures(self):
        self.images = ["images/icons/split_ball_icon_1.png",
                       "images/icons/split_ball_icon_2.png",
                       "images/icons/split_ball_icon_3.png",
                       "images/icons/split_ball_icon_4.png"]
        super().initialize_textures()
        self.frames_per_update = 10

    def activate_icon_property(self):
        self.level.paddle.split_balls += 3


class BonusLifeIcon(Icon):
    """
    Adds an extra life
    """

    def initialize_textures(self):
        self.images = ["images/icons/bonus_life_icon_1.png",
                       "images/icons/bonus_life_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound("audio/sounds/bonus_life_icon_tone.wav")

    def activate_icon_property(self):
        self.level.window.lives += 1


class SafetyBarrierIcon(Icon):
    """
    Activates the safety barrier
    """

    def initialize_textures(self):
        self.images = ["images/icons/safety_barrier_icon_1.png",
                       "images/icons/safety_barrier_icon_2.png",
                       "images/icons/safety_barrier_icon_3.png",
                       "images/icons/safety_barrier_icon_2.png",
                       "images/icons/safety_barrier_icon_1.png",
                       "images/icons/safety_barrier_icon_4.png",
                       "images/icons/safety_barrier_icon_5.png",
                       "images/icons/safety_barrier_icon_6.png",
                       "images/icons/safety_barrier_icon_5.png",
                       "images/icons/safety_barrier_icon_4.png"]
        super().initialize_textures()
        self.frames_per_update = 3

    def activate_icon_property(self):
        self.level.brick_list.append(SafetyBarrier(self.level))


class AdvanceLevelIcon(Icon):
    """
    Advances player to the next level
    """

    def initialize_textures(self):
        self.images = ["images/icons/advance_level_icon_1.png",
                       "images/icons/advance_level_icon_2.png",
                       "images/icons/advance_level_icon_3.png",
                       "images/icons/advance_level_icon_4.png"]
        super().initialize_textures()
        self.frames_per_update = 3

    def activate_icon_property(self):
        # Don't advance level in a demo level
        if not self.level.is_demo_level:
            self.level.level_is_complete()


class SpeedUpBallsIcon(Icon):
    """
    Increases the speed of all the balls. Also makes the paddle non-magnetic
    """

    def initialize_textures(self):
        self.images = ["images/icons/speed_up_ball_icon_1.png",
                       "images/icons/speed_up_ball_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound("audio/sounds/speed_up_icon_tone.wav")

    def activate_icon_property(self):
        self.level.paddle.is_magnetic = False
        self.level.paddle.release_magnetic_balls()

        for ball in self.level.ball_list:
            ball.change_speed("increase")


class SlowDownBallsIcon(Icon):
    """
    Decreases the speed of all the balls
    """

    def initialize_textures(self):
        self.images = ["images/icons/slow_down_ball_icon_1.png",
                       "images/icons/slow_down_ball_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 10
        self.hit_sound = arcade.Sound("audio/sounds/slow_down_icon_tone.wav")

    def activate_icon_property(self):
        for ball in self.level.ball_list:
            ball.change_speed("decrease")


class InvinciBallIcon(Icon):
    """
    Converts a normal ball to an invincible ball for three hits
    """

    def initialize_textures(self):
        self.images = ["images/icons/invincible_ball_icon_1.png",
                       "images/icons/invincible_ball_icon_2.png",
                       "images/icons/invincible_ball_icon_3.png",
                       "images/icons/invincible_ball_icon_2.png"]
        super().initialize_textures()
        self.frames_per_update = 8
        self.hit_sound = arcade.Sound("audio/sounds/invincible_ball_icon_tone.wav")

    def activate_icon_property(self):
        self.level.paddle.invincible_balls += 3

        # In case there are magnetic balls, change them to be invincible
        for ball in self.level.paddle.magnetic_ball_list:
            if not ball.is_invincible:
                new_ball = ball.convert_to(MagneticInviciBall)
                self.level.paddle.magnetic_ball_list.append(new_ball)
                self.level.paddle.magnetic_ball_list.remove(ball)
                self.level.paddle.invincible_balls -= 1


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#                                              EXTRAS

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class SafetyBarrier(Brick, arcade.SpriteSolidColor):
    """
    Creates the safety barrier
    """

    def __init__(self, level: Level, **kwargs):
        super().__init__(level=level, width=1080, height=2, color=arcade.color.WHITE, **kwargs)

        self.center_x = self.level.boundary.center_x
        self.center_y = self.level.boundary.inner_bottom + 7
        self.hit_sound = arcade.Sound("audio/sounds/hit_safety_barrier.wav")
        self.is_safety_barrier = True

    def initialize_textures(self):
        pass


class Bullet(arcade.Sprite):
    """
    Creates a bullet that can destroy bricks
    """

    def __init__(self, level: Level, **kwargs):
        super().__init__("images/icons/bullet.png", scale=0.7, **kwargs)
        self.level = level

        self.center_x = self.level.paddle.center_x
        self.bottom = self.level.paddle.top
        self.change_y = BULLET_SPEED

    def on_update(self, delta_time: float = 1 / 60):
        self.center_y += int(self.change_y * delta_time)

        # Check for collision with bricks
        hit_list = cast(List[Brick], self.collides_with_list(self.level.brick_list))

        if hit_list:
            self.remove_from_sprite_lists()
            for brick in hit_list:
                brick.change_properties()

        # If it goes outside the playing field, remove it
        if self.bottom > self.level.boundary.inner_top:
            self.remove_from_sprite_lists()
