from flask_wtf import FlaskForm
from wtforms import TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired


class KifuForm(FlaskForm):
    kifu = TextAreaField('Paste kifu here', rows=50, cols=50, validators=[DataRequired()])
    delay = FloatField('Time delay between moves, in seconds', default=1.0)
    start = IntegerField('Start position # of the gif', default=0)
    end = IntegerField('End position # of the gif', default=9999)
    submit = SubmitField('Submit')
