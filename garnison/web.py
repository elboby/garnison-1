from flask import Blueprint, current_app, render_template

bp = Blueprint('garnison-web', __name__, template_folder="templates")


@bp.route('/')
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