import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from data import get_tags_used

layout = [
    dcc.Input(
        id="filter-tags",
        placeholder="Filter tags",
        type="text",
        value="",
        className="w-100 pa2 f4",
    ),
    html.Table(
        children=[
            html.Thead(
                children=[
                    html.Tr(
                        children=[
                            html.Th("Tag", className="pv2 ph3 tl f6 fw6 ttu"),
                            html.Th("Regex", className="pv2 ph3 tl f6 fw6 ttu"),
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
    ],
    [
        Input("filter-tags", "value"),
    ],
)
def filter_main_page(filter_value):
    tags_used = get_tags_used()
    return [
        [
            html.Tr(
                children=[
                    html.Td(
                        dcc.Link(row["tag"], href="/{}".format(row["tag_slug"])),
                        className="pv2 ph3",
                    ),
                    html.Td(html.Code(row["Regular expression"]), className="pv2 ph3"),
                    html.Td("{:.0%}".format(row["f1score"]) if row.get("f1score") else "-", className="pv2 ph3 tr"),
                    html.Td("{:.0%}".format(row["precision"]) if row.get("precision") else "-", className="pv2 ph3 tr"),
                    html.Td("{:.0%}".format(row["recall"]) if row.get("precision") else "-", className="pv2 ph3 tr"),
                    html.Td(row["frequency"], className="pv2 ph3 tr"),
                ],
                className="striped--near-white",
            )
            for index, row in tags_used.iterrows()
        ]
    ]
