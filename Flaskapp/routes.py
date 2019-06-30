import secrets
import os
from PIL import Image
from Flaskapp.database_setup import User, Post
from Flaskapp.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flask import render_template, redirect, url_for, flash, request, abort
from Flaskapp import app, bcrypt, db
from flask_login import login_user, current_user, logout_user, login_required

@app.route('/')
def index():
    page = request.args.get('page', 1, type = int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page = page, per_page =5)
    return render_template('index.html', posts=posts)

@app.route('/user/<string:user_name>')
def user_posts(user_name):
    page = request.args.get('page', 1, type = int)
    user = User.query.filter_by(username = user_name).first_or_404()
    posts = Post.query.filter_by(author = user).order_by(Post.date_posted.desc()).paginate(page = page, per_page =5)
    return render_template('user_posts.html', posts=posts, user = user)

@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: 
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashedPassword = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashedPassword)
        db.session.add(user)
        db.session.commit()

        flash(f'Account create for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register',  form=form)


@app.route('/login',  methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome {form.email.data}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else  redirect(url_for('index'))
        else:
            flash("Email or Password is Wrong", 'danger')
    return render_template('login.html', title='Login',  form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash(f'Logout successful', 'danger')
    return redirect(url_for('index'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img/profilepics',picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Information Updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='img/profilepics/'+ current_user.image_file)
    return render_template('account.html', title='account',img = image_file, form = form)

@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title= form.title.data, content = form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post have been Created', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html', title='New Post', form=form,legend = 'New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title= post.title, post = post)

@app.route("/post/update/<int:post_id>", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post have been Updated', 'info')
        return redirect(url_for('post' , post_id = post.id))
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update post', form=form, legend = 'Update Post')



@app.route("/post/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post have been Deleted', 'success')
    return redirect(url_for('index'))