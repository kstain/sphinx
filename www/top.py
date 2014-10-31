from flask import Blueprint
from flask import render_template

from sphinx.www.base import *

home_site = Blueprint('home', 'sphinx.www.home')

@home_site.route('/', methods=['GET'])
def top():
    return render_template('templates/top.html')