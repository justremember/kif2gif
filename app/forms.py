from flask_wtf import FlaskForm
from wtforms import TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired


class KifuForm(FlaskForm):
    kifu = TextAreaField('Paste kifu here', validators=[DataRequired()])
    delay = FloatField('Time delay between moves, in seconds (with millisecond precision)', default=1.0)
    start = IntegerField('Start move # of the gif', default=0)
    end = IntegerField('End move # of the gif', default=9999)
    submit = SubmitField('Submit')
