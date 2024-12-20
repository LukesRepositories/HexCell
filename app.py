from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'for dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = { 'Comment' : 'sqlite:///comments.db', 'Result' : 'sqlite:///results.db', 'Question' : 'sqlite:///questions.db'}
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    public_account = db.Column(db.Boolean, nullable=False)
    results = db.relationship('Result', backref='user', lazy=True) # Defining the relationship for a foreign key
    comments = db.relationship('Comment', backref='user', lazy=True) # Defining the relationship for a foreign key

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey('user.username'), nullable=False)
    content = db.Column(db.String(380), nullable=False)
    likes = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Comment %r>' % self.id


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey('user.username'), nullable=False)
    score = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equation = db.Column(db.String(80))
    equation_evaluated = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect('/')
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template("login.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        password1 = request.form.get('password')
        password2 = request.form.get('passwordReentered')
        if request.form.get('public') == 'checked':
            is_checked = True
        else:
            is_checked = False

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', category='error')
            return render_template("signup.html", user=current_user)
        elif password1 != password2:
            flash('Passwords do not match', category='error')
            return render_template("signup.html", user=current_user)
        elif len(password1) < 8:
            flash('Password must be at least 8 characters.', category='error')
            return render_template("signup.html", user=current_user)
        else:
            try:
                new_user = User(username=username, password=generate_password_hash(password1), public_account=is_checked)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect('/')
            except:
                return 'There was a problem adding your account :('
    else:
        return render_template("signup.html", user=current_user)

# Resets everyday due to Heroku's daily server reset
def setup_equations():
    if Question.query.count() < 6:
        question1num1 = random.randrange(100,9999)
        question1num2 = random.randrange(100, 9999)
        question2num1 = random.randrange(100, 9999)
        question2num2 = random.randrange(100, 9999)
        question3num1 = random.randrange(11, 99)
        question3num2 = random.randrange(11, 99)
        question4num1 = random.randrange(11, 99)
        question4num2 = random.randrange(11, 99)
        question5num1 = random.randrange(11, 99)
        question5num2 = random.randrange(11, 99)
        question6num1 = random.randrange(3, 29)
        question6num2 = random.randrange(3, 29)
        question6num3 = random.randrange(3, 29)
        question6num4 = random.randrange(3, 29)
        question6ops = ["", "", ""]
        for i in range(3):
            if random.randrange(1, 3) == 1:
                question6ops[i] = " + "
            if random.randrange(1, 3) == 2:
                question6ops[i] = " * "
            if random.randrange(1, 4) == 1:
                question6ops[i] = " / "

        equation_list = ["", "", "", "", "", ""]
        equation_list[0] = str(question1num1) + " + " + str(question1num2) + " ="
        equation_list[1] = str(question2num1) + " - " + str(question2num2) + " ="
        equation_list[2] = str(question3num1) + " * " + str(question3num2) + " ="
        equation_list[3] = str(question4num1) + " / " + str(question4num2) + " ="
        equation_list[4] = str(question5num1) + " * " + str(question5num2) + " ="
        equation_list[5] = str(question6num1) + question6ops[0] + str(question6num2) + question6ops[1] + str(question6num3) + question6ops[2] + str(question6num4) + " ="
        evaluated_list = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            temp = equation_list[i][:-2]
            evaluated_list[i] = eval(temp)
            new_question = Question(equation=equation_list[i], equation_evaluated=evaluated_list[i])
            db.session.add(new_question)
        db.session.commit()


@app.route('/maths', methods=['POST'])
@login_required
def check_equations():
    try:
        questions = Question.query.order_by(Question.date).all()  # Fetch all questions
        results = []
        total_score = 0  # Keep track of the user's score

        for i in range(6):
            user_answer = request.form.get(f'math_answer{i}')  # Fetch user input
            if not user_answer:
                flash(f"Answer for question {i + 1} is missing.", category='error')
                continue

            try:
                user_answer = int(user_answer)
                is_correct = user_answer == questions[i].equation_evaluated
                if is_correct:
                    total_score += 1

                # Flash feedback
                if is_correct:
                    flash(f"Question {i + 1}: Correct!", category='success')
                else:
                    flash(f"Question {i + 1}: Incorrect. Correct answer: {questions[i].equation_evaluated}.", category='error')

            except ValueError:
                flash(f"Answer for question {i + 1} is not a valid integer.", category='error')

        # Commit the result to the database
        new_result = Result(username=current_user.username, score=total_score)
        db.session.add(new_result)
        db.session.commit()

        # Render results or redirect
        return render_template('results.html', results=results, user=current_user, score=total_score)
    except Exception as e:
        db.session.rollback()  # Rollback in case of any database errors
        return f"There was an error processing your answers: {str(e)}"


@app.route('/', methods=['POST', 'GET'])
@login_required
def hellow_world():
    if request.method == 'POST':
         if 'comment' in request.form:
            comment_content = request.form['content']
            new_comment = Comment(content=comment_content, username=current_user.username)

            try:
                db.session.add(new_comment)
                db.session.commit()
                return redirect('/')
            except:
                return 'Currently only one comment can be made a day:('

    else:
        setup_equations()
        comments = Comment.query.order_by(Comment.date_created).all()
        questions = Question.query.order_by(Question.date).all()
        return render_template('index.html', comments=comments, questions=questions)



@app.route('/delete/<int:id>')
@login_required
def delete(id):
    comment_to_delete = Comment.query.get_or_404(id)

    try:
        db.session.delete(comment_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting the chosen task'




@app.route('/like/<int:id>')
def like(id):
    comment_to_like = Comment.query.get_or_404(id)

    try:
        comment_to_like.likes = comment_to_like.likes + 1
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting the chosen task'


@app.route('/username/<id>', methods=['GET'])
@login_required
def goto_username_page(id):
    comment = Comment.query.get_or_404(id)
    username = comment.username  # Extract the username from the comment
    return render_template('username.html', username=username)


#@app.errorhandler(404)
#def page_not_found(error):
    #return render_template('/page_not_found'), 404

if __name__ == "__main__":
    app.run(debug=True)


with app.app_context():
    db.create_all()
