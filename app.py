from tagger.index import app

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)