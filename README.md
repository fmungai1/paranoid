# Paranoid

This is a remake of the classic [Paranoid game](https://archive.org/details/msdos_Paranoid_shareware) (1993)
created by The Bit Bucket Brothers (Ben and Tom North).

The game is designed for 1536 x 864 screen resolution - fullscreen.

## Dependencies

Python: 3.8.10

[Arcade](https://api.arcade.academy/en/latest/): 2.4.2

## Resources

Images: Created using MS Paint

Sounds: Recorded using [Audio Converter Program4PC](https://www.program4pc.com/)

Flags: [countryflags.com](https://www.countryflags.com/)

Background Music: [Eric Matyas](https://soundimage.org/)

Sound Effects: [zapsplat.com](https://www.zapsplat.com/)

## How to Run (Developer Mode)

1. Install [Poetry](https://python-poetry.org/) (preferably using [pipx](https://pipx.pypa.io/stable/))

2. Create and activate virtual environment

    ```cmd
    cd paranoid

    poetry env use <path/to/Python38/python.exe>

    poetry shell
    ```

3. Install all dependencies

    ```cmd
    poetry install
    ```

4. Run the game:

    ```cmd
    python src\paranoid\main.py
    ```
