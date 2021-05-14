import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from tagger.app import app
from tagger.data import data_cli
from tagger import page_tags, page_tag, page_main, page_icnptso_all, page_icnptso


base_layout = html.Div(
    children=[
        html.H1(children="Charity Classification tagger"),
        html.Nav(
            children=[
                dcc.Link(
                    "Tags",
                    href=("/tag"),
                    className="link underline-hover",
                ),
                " | ",
                dcc.Link(
                    "ICNPTSO",
                    href=("/icnptso"),
                    className="link underline-hover",
                ),
            ],
            className="mb2 mt0"
        ),
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ],
    className="sans-serif ph4 pv2",
)

app.layout = base_layout
app.server.cli.add_command(data_cli)

app.validation_layout = html.Div(
    [
        base_layout,
        page_main.layout,
        page_tags.layout,
        page_tag.layout,
        page_icnptso_all.layout,
        page_icnptso.layout,
    ]
)


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")],
)
def display_page(pathname):
    if pathname in ("/tag", "/tag/"):
        return page_tags.layout
    if pathname.startswith("/tag/"):
        return page_tag.layout
    if pathname in ("/icnptso", "/icnptso/"):
        return page_icnptso_all.layout
    if pathname.startswith("/icnptso/"):
        return page_icnptso.layout
    return page_main.layout

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
