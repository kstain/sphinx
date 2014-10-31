from flask import Blueprint
from flask import render_template

from sphinx.www.base import *

home_site = Blueprint('home_stub', 'sphinx.www.home_stub')

@test_site.route('/', methods=['GET'])
def home_site():
    return render_template('templates/_top.html')