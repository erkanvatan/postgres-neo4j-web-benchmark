def str_surround(str: str, surround: str = "%", start=True, end=True):
    """Surround a string with a symbol or another string."""

    if start:
        str = surround + str
    if end:
        str = str + surround
    return str


if __name__ == "__main__":
    print("helpers.py main run")
