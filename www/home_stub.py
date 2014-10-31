from flask import Blueprint
from flask import render_template

site = Blueprint('home_site_stub', 'sphinx.www.home_stub')

@site.route('/', methods=['GET'])
def home_site():
    return render_template('_top.html')