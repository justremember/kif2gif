from flask import render_template, redirect, send_from_directory
from app import app
from app.forms import KifuForm
from converter import kif2gif

@app.route('/', methods=['GET', 'POST'])
def index():
    form = KifuForm()
    if form.validate_on_submit():
        gif_filename = kif2gif(form.kifu.data,
                gif_dirname=app.config['GIFS_FOLDER'],
                delay=form.delay.data,
                start=form.start.data,
                end=form.end.data)
        return redirect(gif_filename)
    else:
        print(form.errors)
    return render_template('index.html', form=form)

@app.route('/gifs/<path:filename>')
def download_file(filename):
    return send_from_directory('../' + app.config['GIFS_FOLDER'],
        filename)

