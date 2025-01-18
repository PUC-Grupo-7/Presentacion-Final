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
    region = SelectField(
        'Región',
        choices=[
            ('US', 'Estados Unidos'),
            ('MX', 'México'),
            ('ES', 'España'),
            ('AR', 'Argentina'),
            ('CL', 'Chile'),
            # Agrega más según tus necesidades
        ],
        validators=[DataRequired()],
        default='US'
    )

    submit = SubmitField('Guardar')
