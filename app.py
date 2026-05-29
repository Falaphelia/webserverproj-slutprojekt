from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db

db.init_db() #Make sure database exists / create tables and file if not.

app = Flask(__name__)
debug_mode = True
app.secret_key = "psuK3dIcOpqTWh6K6R3zZhtbqZygtviu" #secure key

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("to_do"))

    return redirect(url_for("login"))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method=="POST":
        email = request.form.get("email").lower() #Make sure you can log in no matter caps in email
        password = request.form.get("password")

        uid = db.login(email, password)

        if not uid:
            flash("Account not found. Perhaps you typed something wrong?", "error")
            return redirect(url_for("login"))
        elif isinstance(uid, str):
            session["user_id"] = uid

        return redirect(url_for("login"))

    return render_template("login.html", title="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/register", methods=['GET', 'POST'])
def register():

    if session.get("user_id"):
        return redirect(url_for("to_do"))

    if request.method == "POST":
        f_name = request.form.get("first_name")
        l_name = request.form.get("last_name")
        email = request.form.get("email").lower()
        password = request.form.get("password")

        all_requirements = f_name and l_name and email and password

        if not all_requirements:
            flash("All requirements not inputed as required", "error")

        answer = db.register_user(f_name, l_name, email, password)

        if not answer:
            flash("User registration failed! An account with this email may already exist or our servers are" \
            " experiencing trouble, please try again soon.", "error")

        return redirect(url_for("login"))

    return render_template("register.html", title="Account Registratiom")

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/to-do", methods=['GET', 'POST'])
def to_do():

    if session.get("user_id") and request.method == "POST":
        pass

    if session.get("user_id"):

        # get all the user's lists

        lists = db.get_user_lists(session.get("user_id"))

        return render_template("to_do.html", title="to-do list", lists=lists)
    else:
        return redirect(url_for("index"))

@app.route("/create-list", methods=["POST"])
def create_list_route():

    list_name = request.form["list_name"]

    if not list_name:
        flash("List name cannot be empty", "error")
        return redirect(url_for("to_do"))

    db.create_list(
        list_name,
        session["user_id"]
    )

    return redirect(url_for("to_do"))

@app.route("/create-entry", methods=["POST"])
def create_entry_route():

    db.create_list_entry(
        request.form["list_id"],
        request.form["content"],
        request.form["description"]
    )

    return redirect(url_for("to_do"))

@app.route("/delete-list", methods=["POST"])
def delete_list_route():

    answer = db.delete_list(
        session["user_id"],
        request.form["list_id"]
    )

    if not answer:
        flash("You are not allowed to delete this list!", "error")

    return redirect(url_for("to_do"))

@app.route("/delete-entry", methods=["POST"])
def delete_entry_route():

    answer = db.delete_list_entry(
        session["user_id"],
        request.form["entry_id"]
    )

    if not answer:
        flash("You are not allowed to delete this entry!", "error")

    return redirect(url_for("to_do"))



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=81, debug=False)
    #Set 'debug=True' to 'debug=False' when putting into production // at submit
    #Set port to 81 instead of standard in case another service is using :80
