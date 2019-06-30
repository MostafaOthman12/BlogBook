from flask import Flask, render_template, redirect, url_for, flash

from Flaskapp import app
if __name__ == "__main__":
    app.run(debug=True, host='localhost', port='5000')
