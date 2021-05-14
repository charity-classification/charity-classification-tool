import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


layout = [
    dcc.Link(
        "Tags",
        href=("/tag"),
        className="link underline-hover w-100 w-20-l fl pa5 shadow-1 mr2 tc f3 db",
    ),
    dcc.Link(
        "ICNPTSO",
        href=("/icnptso"),
        className="link underline-hover w-100 w-20-l fl pa5 shadow-1 mr2 tc f3 db",
    ),
]
