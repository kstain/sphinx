from flask import Blueprint
from flask import render_template

site = Blueprint('home', 'www.home')

@site.route('/')
def index():
    return render_template('index.html')