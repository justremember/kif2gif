from flask import render_template
from app import app
from app.forms import KifuForm

@app.route('/')
@app.route('/index')
def index():
    form = KifuForm
    return render_template('index.html', form=form)
