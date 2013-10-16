from redis import Redis
from flask import Blueprint, render_template, flash, current_app, url_for
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, SelectField, SubmitField
from wtforms.validators import Required

from gachette_web.tasks import init_build_process

blueprint = Blueprint('gachette-web-build', __name__,
                    template_folder="templates")


PROJECTS_DATA = {
    'test_config': {
        'repo': 'git@github.com:ops-hero/test_config.git',
        'path_to_missile': None
    },
    'test_application': {
        'repo': 'git@github.com:ops-hero/test_application.git',
        'path_to_missile': None
    },
}

class BuildForm(Form):
    """
    Form to launch a build of package.
    TODO create a git repo field for validation.
    """
    stack = TextField('Stack', validators=[Required()])
    project = SelectField('Project', 
                    validators=[Required()], 
                    choices=[(k, k) for k in PROJECTS_DATA.iterkeys()])
    app_version = TextField('Application Version', validators=[Required()])
    env_version = TextField('Environment Version', validators=[Required()])
    service_version = TextField('Service Version', validators=[Required()])
    branch = TextField('Branch', default="master", validators=[Required()])
    url = TextField('Repository', validators=[])
    submit_button = SubmitField('Submit Form')


@blueprint.route('/create/', methods=['GET', 'POST'])
def build_create():
    """
    Test. Return status of the builds.
    """
    form = BuildForm(csrf_enabled=False)

    if form.validate_on_submit():

        # variables preparation
        name = "%s-%s" % (form.project.data, form.branch.data)
        project = form.project.data
        url = PROJECTS_DATA[project]['repo'] if form.url.data == "" else form.url.data
        stack = form.stack.data
        branch = form.branch.data
        app_version = form.app_version.data
        env_version = form.env_version.data
        service_version = form.service_version.data
        path_to_missile = PROJECTS_DATA[project]['path_to_missile']
        webcallback = url_for("gachette-web-stack.add_to_stack_call", stack=stack, _external=True)
        print "webcallback: " + webcallback

        # launch async task
        init_build_process(name, stack, project, url, branch,
            app_version, env_version, service_version, path_to_missile,
            webcallback)

        # TODO notifications

        flash("Build successfully created.")
   
    return render_template("build/create.html", form=form)


@blueprint.route('/')
def home():
    """
    Test. Return status of the builds.
    """
    print "toto"
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        print rule.endpoint

    return render_template('index.html')
