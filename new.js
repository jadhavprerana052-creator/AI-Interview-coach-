<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Register - AI Interview Coach</title>

    <link rel="stylesheet"
          href="{{ url_for('static', filename='style.css') }}">

</head>

<body class="auth-body">

<div class="auth-container">

    <div class="auth-card">

        <h1>
            Create Account
        </h1>

        <p>
            Start practicing with your AI interview coach.
        </p>


        {% with messages = get_flashed_messages(with_categories=true) %}

            {% for category, message in messages %}

                <div class="alert {{ category }}">
                    {{ message }}
                </div>

            {% endfor %}

        {% endwith %}


        <form method="POST">

            <label>
                Full Name
            </label>

            <input
                type="text"
                name="name"
                placeholder="Your name"
                required
            >


            <label>
                Email
            </label>

            <input
                type="email"
                name="email"
                placeholder="you@example.com"
                required
            >


            <label>
                Password
            </label>

            <input
                type="password"
                name="password"
                placeholder="Create password"
                minlength="6"
                required
            >


            <button class="btn full">
                Create Account
            </button>

        </form>


        <p class="auth-footer">

            Already have an account?

            <a href="{{ url_for('login') }}">
                Login
            </a>

        </p>

    </div>

</div>

</body>
</html>