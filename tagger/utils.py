import re

import dash_html_components as html


def stats_box(stat, title, link=None):
    className = "tc ph4 pv3 fl mr3 "
    colours = stat_colour(stat)
    className += colours
    if link:
        title = html.A(
            title,
            href=link,
            className=colours,
            target="_blank",
        )
    return html.Div(
        children=[
            html.Div(
                "{:,.0%}".format(stat),
                className="f2 b",
            ),
            html.Div(title, className="f4"),
        ],
        className=className,
    )


def stat_colour(stat):
    if stat > 0.75:
        return "bg-washed-green dark-green"
    elif stat > 0.5:
        return "bg-washed-yellow orange"
    return "bg-washed-red dark-red"


def highlight_regex(text, regex):
    def span_match(m):
        return '<span class="bg-light-pink i">' + m.group(0) + "</span>"

    return re.sub(
        regex,
        span_match,
        text,
        flags=re.IGNORECASE,
    )


def get_tag_name(row):
    parts = [row["Category"]]
    if isinstance(row["Subcategory"], str) and row["tag"].lower() != row["Subcategory"].lower():
        parts.append(row["Subcategory"])
    if row["tag"].lower() != row["Category"].lower():
        parts.append(row["tag"])
    return " - ".join(parts)
