import re

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
from slugify import slugify
import pandas as pd

from tagger.app import app
from tagger.data import (
    RESULT_TYPES,
    get_keyword_result,
    get_result_summary,
    save_regex_to_airtable,
    get_tags_used,
    get_completed_data,
    save_tags_used,
    get_all_charities,
)
from tagger.utils import stats_box, highlight_regex
from tagger.settings import DEFAULT_REGEX, TAGS_FIELD_NAME


layout = [
    dcc.Link("< Back to home", href="/"),
    html.H2(id="tag-header"),
    html.Div(
        [
            html.Label(
                [
                    html.Strong("Include"),
                    " any charity name and activities matching this regular expression",
                ],
                htmlFor="tag-regex",
            ),
            dcc.Input(
                id="tag-regex",
                placeholder="regex_search",
                type="text",
                value=DEFAULT_REGEX,
                className="w-100 pa2 f4 code",
                debounce=True,
            ),
        ],
        className="mv3",
    ),
    html.Div(
        [
            html.Label(
                [
                    html.Strong("Exclude"),
                    " any charity name and activities matching this regular expression",
                ],
                htmlFor="tag-regex",
            ),
            dcc.Input(
                id="tag-regex-exclude",
                placeholder="regex_search",
                type="text",
                value=DEFAULT_REGEX,
                className="w-100 pa1 f5 code",
                debounce=True,
            ),
        ],
        className="mv3",
    ),
    html.Div(id="result-summary", className="cf mv3"),
    dcc.Tabs(
        id="result-tab-select",
        value="sample-match",
        children=[
            dcc.Tab(label="Sample results", value="sample-match"),
            dcc.Tab(label="Match against all charities", value="all-charity-match"),
        ],
        className="mv3",
    ),
    html.Div(id="result-tab-content", className="flex flex-wrap"),
]


@app.callback(
    [
        Output("tag-regex", "value"),
        Output("tag-regex-exclude", "value"),
    ],
    [Input("url", "pathname")],
)
def tag_regex_setup(pathname):
    tag_regex = [DEFAULT_REGEX, ""]
    tags_used = get_tags_used()
    tag_slug = pathname[5:]
    if tag_slug not in tags_used["tag_slug"].unique():
        return tag_regex
    tag_regex[0] = tags_used.loc[
        tags_used["tag_slug"] == tag_slug, "Regular expression"
    ].iloc[0]
    tag_regex[1] = tags_used.loc[
        tags_used["tag_slug"] == tag_slug, "Exclude regular expression"
    ].iloc[0]
    if not tag_regex[0] or pd.isna(tag_regex[0]):
        tag_regex[0] = DEFAULT_REGEX
    if not tag_regex[1] or pd.isna(tag_regex[1]):
        tag_regex[1] = ""
    return tag_regex


@app.callback(
    [
        Output("tag-header", "children"),
        Output("result-summary", "children"),
        Output("result-tab-content", "children"),
    ],
    [
        Input("tag-regex", "value"),
        Input("tag-regex-exclude", "value"),
        Input("result-tab-select", "value"),
    ],
    [
        State("url", "pathname"),
    ],
)
def tag_regex_page(keyword_regex, exclude_regex, result_tab, pathname):
    tags_used = get_tags_used()
    df, corpus = get_completed_data()
    tag_slug = pathname[5:]
    try:
        tag = tags_used.loc[tags_used["tag_slug"] == tag_slug, :].iloc[0]
    except IndexError as e:
        return (
            [
                None,
                None,
            ]
            + [None for r in RESULT_TYPES.keys()]
            + [None for r in RESULT_TYPES.keys()]
        )
    try:
        result = get_keyword_result(
            tag["tag"], keyword_regex, exclude_regex, df, corpus
        )
    except re.error as err:
        return ([tag["tag"], html.Div(str(err), className="bg-red white pa3")], [])
    result_summary = get_result_summary(result)
    tags_used.loc[tag.name, "Regular expression"] = keyword_regex
    tags_used.loc[tag.name, "precision"] = result_summary["precision"]
    tags_used.loc[tag.name, "recall"] = result_summary["recall"]
    tags_used.loc[tag.name, "f1score"] = result_summary["f1score"]
    tags_used.loc[tag.name, "accuracy"] = result_summary["accuracy"]
    save_regex_to_airtable(tag.name, keyword_regex, exclude_regex)
    save_tags_used(tags_used)

    # get tab content
    if result_tab == "all-charity-match":
        all_charities, all_charities_group = get_all_charities(keyword_regex, exclude_regex)
        result_tab_content = [
            html.Div([
                html.P("{:,.2%} of charities match this tag ({:,.0f} estimated)".format(
                    all_charities_group.loc["Total", "percentage"],
                    all_charities_group.loc["Total", "estimated_total"],
                ), className="w-100"),
                html.Table([
                    html.Tr([
                        html.Th("Income band", className="pv2 ph3"),
                        html.Th("Proportion matching", className="pv2 ph3"),
                        html.Th("Estimated total", className="pv2 ph3"),
                    ])
                ] + [
                    html.Tr([
                        html.Th(index, className="pv2 ph3"),
                        html.Td("{:,.2%}".format(row["percentage"]), className="pv2 ph3 tr"),
                        html.Td("{:,.0f}".format(row["estimated_total"]), className="pv2 ph3 tr"),
                    ], className="striped--light-gray ") for index, row in all_charities_group.iterrows()
                ], className="collapse"),
            ], className="w-100"),
            html.Ul([
                html.Li(
                    children=[
                        html.H4(
                            DangerouslySetInnerHTML(
                                highlight_regex(
                                    row["name"], keyword_regex
                                ),
                            ),
                        ),
                        html.P(
                            DangerouslySetInnerHTML(
                                highlight_regex(
                                    row["activities"], keyword_regex
                                ),
                            ),
                            className="f6",
                        ),
                    ],
                    className="mv2 mw6",
                )
                for index, row in all_charities.iterrows()
            ], style={"columns": 4})
        ]
    else:
        result_tab_content = [
            html.Div(
                children=[
                    html.H3(
                        children="{:,.0f} {}{}".format(
                            result_summary[r],
                            r.replace("-", " "),
                            "s" if result_summary[r] != 1 else "",
                        ),
                        id="{}-header".format(r),
                    ),
                    html.P(
                        children=description,
                        className="i f6 gray",
                    ),
                    html.Div(
                        html.Ul(
                            children=[
                                html.Li(
                                    children=[
                                        html.H4(
                                            DangerouslySetInnerHTML(
                                                highlight_regex(
                                                    row["name"], keyword_regex
                                                ),
                                            ),
                                        ),
                                        html.P(
                                            DangerouslySetInnerHTML(
                                                highlight_regex(
                                                    row["activities"], keyword_regex
                                                ),
                                            ),
                                            className="f6",
                                        ),
                                        html.Ul(
                                            [
                                                html.Li(
                                                    dcc.Link(
                                                        t,
                                                        href=("/tag/" + slugify(t)),
                                                        className="white link underline-hover",
                                                    ),
                                                    className="dib pa1 bg-blue white mr1 mb1",
                                                )
                                                for t in row[TAGS_FIELD_NAME]
                                            ],
                                            className="list ma0 pa0 f6",
                                        ),
                                    ],
                                    className="mv2",
                                )
                                for index, row in df.loc[result["result"] == r, :]
                                .head(10)
                                .iterrows()
                            ],
                            className="list pa0 ma0",
                        )
                    ),
                ],
                className="w-25-l w-50 pr3",
            )
            for r, description in RESULT_TYPES.items()
        ]

    return [
        tag["tag"],
        [
            html.P(
                "{:,.0f} records are tagged with {}".format(
                    result_summary["relevant"], tag["tag"]
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
        result_tab_content,
    ]
