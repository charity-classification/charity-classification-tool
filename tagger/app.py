import dash

external_stylesheets = ["https://unpkg.com/tachyons@4.12.0/css/tachyons.min.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
