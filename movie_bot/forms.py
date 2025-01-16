# movie_bot/forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class ProfileForm(FlaskForm):
    favorite_genre = SelectField(
        'Género Favorito',
        choices=[
            ('accion', 'Acción'),
            ('comedia', 'Comedia'),
            ('drama', 'Drama'),
            ('terror', 'Terror'),
            ('suspenso', 'Suspenso'),
            ('romance', 'Romance')
        ],
        validators=[DataRequired()]
    )
    disliked_genre = SelectField(
        'Género a Evitar',
        choices=[
            ('accion', 'Acción'),
            ('comedia', 'Comedia'),
            ('drama', 'Drama'),
            ('terror', 'Terror'),
            ('suspenso', 'Suspenso'),
            ('romance', 'Romance')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Guardar')
