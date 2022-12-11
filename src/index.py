import app
import waitress

if __name__ == "__main__":
    waitress.serve(app=app.app, host='0.0.0.0', port=8050)