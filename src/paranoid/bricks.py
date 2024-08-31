"""
The different types of bricks used in the game.

Created using MS Paint app

Images for flags downloaded from: https://www.countryflags.com/ and resized using MS Paint app
Colors obtained using color picker on the original game
"""

# Allows specifying of type checking hints without having to use string literals,
# e.g "Level" in Brick `__init__` method
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING

import arcade

from paranoid.constants import (
    AUDIO_BASE_PATH,
    IMAGES_BASE_PATH,
    NORMAL_VOLUME,
)

# Prevents circular import error by setting this variable False at runtime
if TYPE_CHECKING:
    from paranoid.icons import Icon
    from paranoid.levels import Level


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
