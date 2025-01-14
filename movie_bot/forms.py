# movie_bot/forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class ProfileForm(FlaskForm):
    favorite_genre = SelectField(
        'Género Favorito',
        choices=[
            ('Acción', 'Acción'),
            ('Comedia', 'Comedia'),
            ('Drama', 'Drama'),
            ('Terror', 'Terror'),
            ('Suspenso', 'Suspenso'),
            ('Romance', 'Romance')
        ],
        validators=[DataRequired()]
    )
    disliked_genre = SelectField(
        'Género a Evitar',
        choices=[
            ('Acción', 'Acción'),
            ('Comedia', 'Comedia'),
            ('Drama', 'Drama'),
            ('Terror', 'Terror'),
            ('Suspenso', 'Suspenso'),
            ('Romance', 'Romance')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Guardar')
