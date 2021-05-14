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
    get_icnptso_used,
    get_completed_data,
    save_icnptso_used,
    get_all_charities,
)
from tagger.utils import stats_box, highlight_regex, get_icnptso_name
from tagger.settings import AIRTABLE_ICNPTSO_TABLE_NAME, DEFAULT_REGEX, ICNPTSO_FIELD_NAME


layout = [
    dcc.Link("< Back to ICNPTSO", href="/icnptso"),
    html.H2(id="category-header"),
    html.Div(
        [
            html.Label(
                [
                    html.Strong("Include"),
                    " any charity name and activities matching this regular expression",
                ],
                htmlFor="category-regex",
            ),
            dcc.Textarea(
                id="category-regex",
                placeholder="regex_search",
                value=DEFAULT_REGEX,
                className="w-100 pa2 f4 code",
                style={"word-break": "break-all"},
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
                htmlFor="category-regex-exclude",
            ),
            dcc.Textarea(
                id="category-regex-exclude",
                placeholder="regex_search",
                value=DEFAULT_REGEX,
                className="w-100 pa1 f5 code",
                style={"word-break": "break-all"},
            ),
        ],
        className="mv3",
    ),
    html.Div(id="category-result-summary", className="cf mv3"),
    dcc.Tabs(
        id="result-tab-select",
        value="sample-match",
        children=[
            dcc.Tab(label="Sample results", value="sample-match"),
            dcc.Tab(label="Match against all charities", value="all-charity-match"),
        ],
        className="mv3",
    ),
    html.Div(id="category-result-tab-content", className="flex flex-wrap"),
]


@app.callback(
    [
        Output("category-regex", "value"),
        Output("category-regex-exclude", "value"),
    ],
    [Input("url", "pathname")],
)
def category_regex_setup(pathname):
    category_regex = [DEFAULT_REGEX, ""]
    categories_used = get_icnptso_used()
    category_slug = pathname[9:]
    if category_slug not in categories_used["Code"].unique():
        return category_regex
    category_regex[0] = categories_used.loc[
        categories_used["Code"] == category_slug, "Regular expression"
    ].iloc[0]
    if categories_used.get("Exclude regular expression"):
        category_regex[1] = categories_used.loc[
            categories_used["Code"] == category_slug, "Exclude regular expression"
        ].iloc[0]
    if not category_regex[0] or pd.isna(category_regex[0]):
        category_regex[0] = DEFAULT_REGEX
    if not category_regex[1] or pd.isna(category_regex[1]):
        category_regex[1] = ""
    return category_regex


@app.callback(
    [
        Output("category-header", "children"),
        Output("category-result-summary", "children"),
        Output("category-result-tab-content", "children"),
    ],
    [
        Input("category-regex", "n_blur"),
        Input("category-regex-exclude", "n_blur"),
        Input("result-tab-select", "value"),
    ],
    [
        Input("category-regex", "value"),
        Input("category-regex-exclude", "value"),
        State("url", "pathname"),
    ],
)
def tag_regex_page(_, __, result_tab, keyword_regex, exclude_regex, pathname):
    categories_used = get_icnptso_used()
    df, corpus = get_completed_data()
    category_slug = pathname[9:]
    try:
        category = categories_used.loc[categories_used["Code"] == category_slug, :].iloc[0]
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
            keyword_regex,
            exclude_regex,
            df,
            corpus,
            icnptso=category["Code"],
        )
    except re.error as err:
        return ([get_icnptso_name(category), html.Div(str(err), className="bg-red white pa3")], [])
    result_summary = get_result_summary(result)
    categories_used.loc[category.name, "Regular expression"] = keyword_regex
    categories_used.loc[category.name, "precision"] = result_summary["precision"]
    categories_used.loc[category.name, "recall"] = result_summary["recall"]
    categories_used.loc[category.name, "f1score"] = result_summary["f1score"]
    categories_used.loc[category.name, "accuracy"] = result_summary["accuracy"]
    save_regex_to_airtable(category.name, keyword_regex, exclude_regex, AIRTABLE_ICNPTSO_TABLE_NAME)
    save_icnptso_used(categories_used)

    # get tab content
    if result_tab == "all-charity-match":
        all_charities, all_charities_group = get_all_charities(keyword_regex, exclude_regex)
        result_tab_content = [
            html.Div([
                html.P("{:,.2%} of charities match this category ({:,.0f} estimated)".format(
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
                                                        row[ICNPTSO_FIELD_NAME],
                                                        href=("/icnptso/" + row[ICNPTSO_FIELD_NAME]),
                                                        className="white link underline-hover",
                                                    ),
                                                    className="dib pa1 bg-blue white mr1 mb1",
                                                )
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
        get_icnptso_name(category),
        [
            html.P(
                "{:,.0f} records are tagged with {}".format(
                    result_summary["relevant"], category["Code"]
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
