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

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    TYPE_CHECKING,
    cast,
)

import arcade

from paranoid.balls import (
    Ball,
    InvinciBall,
    MagneticInvinciBall,
    NormalBall,
)
from paranoid.constants import (
    AUDIO_BASE_PATH,
    BULLET_SPEED,
    ICON_SPEED,
    IMAGES_BASE_PATH,
    NORMAL_VOLUME,
    PADDLE_SPEED,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.levels import Level


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
