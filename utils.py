from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

def secretary_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ["secretary", "admin"]:
            flash("Access denied", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated
