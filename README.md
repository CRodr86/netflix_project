# My Flask Project

This is a simple Flask project, equipped with SQLAlchemy, Flask-Migrate, and other extensions for rapid development.

## Prerequisites

- Python 3.10
- Pipenv

## Getting Started

### Clone the Repository

First, clone the repository to your local machine:

\`\`\`bash
git clone https://github.com/yourusername/yourprojectname.git
\`\`\`

Navigate to the project folder:

\`\`\`bash
cd yourprojectname
\`\`\`

### Create and Activate Virtual Environment

Create a new virtual environment using Pipenv:

\`\`\`bash
pipenv shell
\`\`\`

This command will create a new virtual environment and activate it.

### Install Dependencies

Now install the project dependencies:

\`\`\`bash
pipenv install
\`\`\`

This will install all the packages listed in the `Pipfile` and their specific versions listed in `Pipfile.lock`.

### Environment Variables

Make sure to set up the required environment variables or place them in a `.env` file within your project directory. Here's an example `.env` file:

\`\`\`env
FLASK_APP=app.py
DATABASE_URL=postgresql://localhost/mydatabase
SECRET_KEY=mysecretkey
\`\`\`

### Initialize Database

Run the following command to initialize the database:

\`\`\`bash
pipenv run init
\`\`\`

### Run Migrations

Run the following commands to migrate the database:

\`\`\`bash
pipenv run migrate
pipenv run upgrade
\`\`\`

### Running the Project

Now, you can run the project using:

\`\`\`bash
pipenv run start
\`\`\`

This will start the Flask application on `http://0.0.0.0:3001/`.

---

### Test user
username: testuser
email: testuser@testmail.com
password: test