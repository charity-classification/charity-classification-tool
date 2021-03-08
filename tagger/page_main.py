import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from tagger.app import app
from tagger.data import tags_used
from tagger.utils import stat_colour

layout = [
    html.Div([
        html.Div([
            dcc.Input(
                id="filter-tags",
                placeholder="Filter tags",
                type="text",
                value="",
                className="w-100 pa2 f4 dn",
            ),
            html.Div([
                # html.Label("Filter by regular expression", htmlFor="show-rows", className="f5 b pb2 db cf"),
                dcc.RadioItems(
                    id="show-rows",
                    options=[
                        {"value": "all", "label": "Show all rows"},
                        {"value": "with", "label": "Only with regex"},
                        {"value": "without", "label": "Without regex"},
                    ],
                    value="all",
                    inputClassName="mr1",
                    labelClassName="mr2",
                    className="cf",
                ),
            ], className="f6 mv2"),
            html.Div([
                html.Label("Sort by", htmlFor="show-rows", className="f5 b pb2 mt3 db cf"),
                dcc.Dropdown(
                    id="order-by",
                    options=[
                        {"value": "frequency", "label": "Frequency"},
                        {"value": "tag", "label": "Tag name"},
                        {"value": "f1score", "label": "F1 score"},
                        {"value": "precision", "label": "Precision"},
                        {"value": "recall", "label": "Recall"},
                    ],
                    value="frequency",
                    className="mw5 mb1",
                ),
                dcc.RadioItems(
                    id="order-by-direction",
                    options=[
                        {"label": "Ascending", "value": "ascending"},
                        {"label": "Descending", "value": "descending"},
                    ],
                    value="descending",
                    inputClassName="mr1",
                    labelClassName="mr2",
                    className="cf",
                ),
            ], className="f6 mv2"),
        ], className="w-75-l w-100 fl"),
        html.Div(id="tag-stats", className="w-25-l w-100 fl tr-l"),
    ]),
    html.Table(
        children=[
            html.Thead(
                children=[
                    html.Tr(
                        children=[
                            html.Th("Tag", className="pv2 ph3 tl f6 fw6 ttu"),
                            html.Th("Regex", className="pv2 ph3 tl f6 fw6 ttu mw6"),
                            html.Th("F1", className="pv2 ph3 tl f6 fw6 ttu tr"),
                            html.Th("Precision", className="pv2 ph3 tl f6 fw6 ttu tr"),
                            html.Th("Recall", className="pv2 ph3 tl f6 fw6 ttu tr"),
                            html.Th("Frequency", className="pv2 ph3 tl f6 fw6 ttu tr"),
                        ]
                    )
                ]
            ),
            html.Tbody(
                id="tags-to-choose",
                children=[],
            ),
        ],
        className="collapse ba br2 b--black-10 pv2 ph3 mt4",
    ),
]


@app.callback(
    [
        Output("tags-to-choose", "children"),
        Output("tag-stats", "children"),
    ],
    [
        Input("filter-tags", "value"),
        Input("show-rows", "value"),
        Input("order-by", "value"),
        Input("order-by-direction", "value"),
    ],
)
def filter_main_page(filter_value, show_rows_regex, order_by, order_by_direction):
    def stat_cell(row, field):
        className = "pv2 ph3 tr "
        if not isinstance(row.get(field), float):
            return html.Td("-", className=className)
        value = row[field]
        colour = stat_colour(value)
        return html.Td("{:.0%}".format(value), className=className + colour)

    rows_to_show = tags_used.copy()
    if show_rows_regex == "with":
        rows_to_show = rows_to_show[rows_to_show["Regular expression"].notnull()]
    elif show_rows_regex == "without":
        rows_to_show = rows_to_show[rows_to_show["Regular expression"].isnull()]

    if order_by not in ["frequency", "tag", "f1score", "precision", "recall"]:
        order_by = "tag"

    rows_to_show = rows_to_show.sort_values(
        order_by, ascending=(order_by_direction == "ascending")
    )

    return [
        [
            html.Tr(
                children=[
                    html.Td(
                        dcc.Link(row["tag"], href="/{}".format(row["tag_slug"])),
                        className="pv2 ph3",
                    ),
                    html.Td(html.Code(row["Regular expression"]), className="pv2 ph3 mw6", style={"word-break": "break-word"}),
                    stat_cell(row, "f1score"),
                    stat_cell(row, "precision"),
                    stat_cell(row, "recall"),
                    html.Td(row["frequency"], className="pv2 ph3 tr"),
                ],
                className="striped--near-white",
            )
            for index, row in rows_to_show.iterrows()
        ],
        [
            html.Ul(
                [
                    html.Li([
                        "Showing {:,.0f} of {:,.0f} tags".format(
                            len(rows_to_show),
                            len(tags_used),
                        )
                    ]),
                    html.Li([
                        "{:,.0f} have regular expressions".format(len(tags_used[tags_used["Regular expression"].notnull()]))
                    ]),
                    html.Li([
                        "{:,.0f} need regular expressions".format(len(tags_used[tags_used["Regular expression"].isnull()]))
                    ]),
                    html.Li([
                        "Median F1 score: {:.0%}".format(tags_used["f1score"].median())
                    ]),
                    html.Li([
                        "Median precision: {:.0%}".format(tags_used["precision"].median())
                    ]),
                    html.Li([
                        "Median recall: {:.0%}".format(tags_used["recall"].median())
                    ]),
                ],
                className="list ma0 pa0"
            )
        ]
    ]
