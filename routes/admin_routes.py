from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
