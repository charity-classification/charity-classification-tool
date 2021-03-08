import re

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
from slugify import slugify

from app import app
from data import RESULT_TYPES, get_keyword_result, get_result_summary, tags_used, df
from utils import stats_box, highlight_regex


layout = [
    dcc.Link("< Back to home", href="/"),
    html.H2(id="tag-header"),
    html.Div(
        [
            html.Label(
                "Regular expression will be checked against charity name and activities",
                htmlFor="tag-regex",
            ),
            dcc.Input(
                id="tag-regex",
                placeholder="regex_search",
                type="text",
                value=r"\b()\b",
                className="w-100 pa2 f4 code",
            ),
        ],
        className="mv3",
    ),
    html.Div(id="result-summary", className="cf mv3"),
    html.Div(
        children=[
            html.Div(
                children=[
                    html.H3(
                        children=r.replace("-", " "),
                        id="{}-header".format(r),
                    ),
                    html.P(
                        children=description,
                        className="i f6 gray",
                    ),
                    html.Div(id="{}-list".format(r)),
                ],
                className="w-25-l w-50 pr3",
            )
            for r, description in RESULT_TYPES.items()
        ],
        className="flex flex-wrap",
    ),
]


@app.callback(
    [
        Output("tag-header", "children"),
        Output("result-summary", "children"),
    ]
    + [Output("{}-header".format(r), "children") for r in RESULT_TYPES.keys()]
    + [Output("{}-list".format(r), "children") for r in RESULT_TYPES.keys()],
    [
        Input("tag-regex", "value"),
    ],
    [
        State("url", "pathname"),
    ],
)
def tag_regex_page(keyword_regex, pathname):
    tag_slug = pathname[1:]
    tag = tags_used.loc[tags_used["tag_slug"] == tag_slug, "tag"].iloc[0]
    try:
        result = get_keyword_result(tag, keyword_regex)
    except re.error as err:
        return (
            [tag, html.Div(str(err), className="bg-red white pa3")]
            + [r.replace("-", " ") for r in RESULT_TYPES.keys()]
            + [None for result_type in RESULT_TYPES.keys()]
        )
    result_summary = get_result_summary(result)
    return (
        [
            tag,
            [
                html.P(
                    "{:,.0f} records are tagged with {}".format(
                        result_summary["relevant"], tag
                    )
                ),
                html.P(
                    [
                        "{:,.0f} records selected by the regular expression ".format(
                            result_summary["selected"]
                        ),
                        html.Code(keyword_regex, className="bg-light-gray pa1"),
                    ]
                ),
                html.Div(
                    [
                        stats_box(
                            result_summary["f1score"],
                            "F1",
                            "https://en.wikipedia.org/wiki/F-score",
                        ),
                        stats_box(
                            result_summary["precision"],
                            "Precision",
                            "https://en.wikipedia.org/wiki/Precision_and_recall#Precision",
                        ),
                        stats_box(
                            result_summary["recall"],
                            "Recall",
                            "https://en.wikipedia.org/wiki/Precision_and_recall#Recall",
                        ),
                        stats_box(result_summary["accuracy"], "Accuracy"),
                    ],
                    className="cf",
                ),
            ],
        ]
        + [
            "{:,.0f} {}{}".format(
                result_summary[r],
                r.replace("-", " "),
                "s" if result_summary[r] != 1 else "",
            )
            for r in RESULT_TYPES.keys()
        ]
        + [
            html.Ul(
                children=[
                    html.Li(
                        children=[
                            html.H4(
                                DangerouslySetInnerHTML(
                                    highlight_regex(row["name"], keyword_regex),
                                ),
                            ),
                            html.P(
                                DangerouslySetInnerHTML(
                                    highlight_regex(row["activities"], keyword_regex),
                                ),
                                className="f6",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        dcc.Link(
                                            t,
                                            href=("/" + slugify(t)),
                                            className="white link underline-hover",
                                        ),
                                        className="dib pa1 bg-blue white mr1 mb1",
                                    )
                                    for t in row["Tags"]
                                ],
                                className="list ma0 pa0 f6",
                            ),
                        ],
                        className="mv2",
                    )
                    for index, row in df.loc[result["result"] == result_type, :]
                    .head(10)
                    .iterrows()
                ],
                className="list pa0 ma0",
            )
            for result_type in RESULT_TYPES.keys()
        ]
    )