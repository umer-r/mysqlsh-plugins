"""
lib/output.py — Terminal output / formatting helpers.

Keeps all display logic (ASCII tables, section headers) out of command
files so the visual style is consistent and easy to change in one place.
"""


def print_table(headers, rows):
    """
    Print a plain ASCII table to stdout.

    Args:
        headers (list[str]): Column header labels.
        rows (list[list]): Each inner list is one data row; values are
                           coerced to str automatically.
    """
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def _format_row(data):
        return "| " + " | ".join(
            str(v).ljust(w) for v, w in zip(data, col_widths)
        ) + " |"

    print(separator)
    print(_format_row(headers))
    print(separator)
    for row in rows:
        print(_format_row(row))
    print(separator)


def print_section(title, width=60):
    """
    Print a labelled section divider.

    Args:
        title (str): The section label to display.
        width (int): Character width of the divider line.
    """
    print("\n{}".format(title))
    print("-" * width)
