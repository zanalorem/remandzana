import time

from wtforms import validators, widgets, Form, ValidationError
from wtforms import StringField, IntegerField, BooleanField, TextAreaField

from .models.person import Person
from .auth import check_signature


class Send(Form):
    message = StringField(
        validators=[
            validators.input_required(),
            validators.length(max=500)
        ]
    )
    clavis = StringField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )
    timestamp = IntegerField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )
    setup = BooleanField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )
    salt = StringField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )
    signature = StringField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )

    def validate_clavis(self, clavis):
        clavis.person = Person._ALL_PEOPLE.get(clavis.data)
        if clavis.person is None:
            raise ValidationError(f"Nonexistent person: {clavis.data}")

    def validate_timestamp(self, timestamp):
        if int(time.time()) - timestamp.data >= 86400:
            raise ValidationError(f"Timestamp too old: {timestamp.data}")

    def validate_signature(self, signature):
        ok = check_signature(
            signature=signature.data,
            timestamp=self.timestamp.data,
            clavis=self.clavis.data,
            role_setup=self.setup.data,
            salt=self.salt.data
        )
        if not ok:
            raise ValidationError(f"Invalid signature: {signature.data}")


class Feedback(Form):
    message = TextAreaField(
        validators=[
            validators.input_required(),
            validators.length(max=500),
        ]
    )
    salt = StringField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )
    signature = StringField(
        validators=[validators.input_required()],
        widget=widgets.HiddenInput()
    )

    def validate_signature(self, signature):
        ok = check_signature(
            signature=signature.data,
            timestamp=None,
            clavis=None,
            role_setup=None,
            salt=self.salt.data
        )
        if not ok:
            raise ValidationError(
                f"Invalid feedback signature: {signature.data}"
            )
