import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from tagger.app import app
from tagger.data import data_cli
from tagger import page_main, page_tag


base_layout = html.Div(
    children=[
        html.H1(children="Charity Classification tagger"),
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
        page_tag.layout,
    ]
)


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")],
)
def display_page(pathname):
    if pathname.startswith("/tag/"):
        return page_tag.layout
    return page_main.layout

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
