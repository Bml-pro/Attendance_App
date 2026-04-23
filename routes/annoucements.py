from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date
from yourapp import db
from yourapp.models import Announcement
from yourapp.decorators import secretary_required
from flask_login import current_user

announcements_bp = Blueprint("announcements", __name__)

@announcements_bp.route("/announcements")
@secretary_required
def announcements():
    data = Announcement.query.order_by(Announcement.publish_date.desc()).all()
    return render_template("announcements/list.html", announcements=data)


@announcements_bp.route("/announcements/new", methods=["GET", "POST"])
@secretary_required
def new_announcement():
    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        expiry = request.form.get("expiry_date")

        ann = Announcement(
            title=title,
            message=message,
            expiry_date=expiry if expiry else None,
            created_by=current_user.id
        )
        db.session.add(ann)
        db.session.commit()

        flash("Announcement published", "success")
        return redirect(url_for("announcements.announcements"))

    return render_template("announcements/new.html")


@announcements_bp.route("/announcements/delete/<int:id>")
@secretary_required
def delete_announcement(id):
    ann = Announcement.query.get_or_404(id)
    db.session.delete(ann)
    db.session.commit()
    flash("Announcement deleted", "info")
    return redirect(url_for("announcements.announcements"))
