# Paranoid

This is a remake of the classic [Paranoid game](https://archive.org/details/msdos_Paranoid_shareware)
(1993) created by The Bit Bucket Brothers (Ben and Tom North).

The game is designed for 1536 x 864 screen resolution - fullscreen.

## Dependencies

Python: 3.10.4

[Arcade](https://api.arcade.academy/en/latest/): 2.6.17

## Resources

Images: Created using MS Paint

Sounds: Recorded using [Audio Converter Program4PC](https://www.program4pc.com/)

Flags: [countryflags.com](https://www.countryflags.com/)

Background Music: [Eric Matyas](https://soundimage.org/)

Sound Effects: [zapsplat.com](https://www.zapsplat.com/)

## How to Run (Developer Mode)

1. Install [Poetry](https://python-poetry.org/) (preferably using [pipx](https://pipx.pypa.io/stable/))

2. Clone this repository

    ```cmd
    git clone https://github.com/fmungai1/paranoid.git

    cd paranoid
    ```

3. Create and activate virtual environment

    ```cmd
    poetry env use <path/to/Python310/python.exe>

    poetry shell
    ```

4. Install all dependencies

    ```cmd
    poetry install
    ```

5. Set up pre-commit

    ```cmd
    pre-commit install
    ```

6. Run the game:

    ```cmd
    python src\paranoid\main.py
    ```
