from flask import Flask, render_template, request, redirect, url_for, flash #Flask library and functions
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash #This library lets us easily hash + verify passwords
import sqlite3 #Our database
import datetime #Used to display current date & time
import requests #Used for API calls

#Instantiate Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_a_very_secret_key' #Needed to implement flash messages

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Connection to DB
connection = sqlite3.connect('BeanBrew.db', check_same_thread=False) #Will create DB if it doesn't already exist

#Set up tables if they don't exist already
query = """CREATE TABLE IF NOT EXISTS
    users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL)"""
cursor = connection.cursor()
cursor.execute(query)
query = """CREATE TABLE IF NOT EXISTS product(id INTEGER PRIMARY KEY, productName TEXT NOT NULL, productDescription TEXT NOT NULL, price REAL NOT NULL);"""
cursor.execute(query)
cursor.close() #Important to make sure we close the cursor when we are done with it.

def getCurrentDateTime():
    date = datetime.datetime.now().date()
    time = datetime.datetime.now().time()
    return date.strftime("%d/%m/%Y"), time.strftime("%X") #Format the date and time correctly before returning.

def getProducts(): #Query our table to retrieve all of our products
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Product")
        products = cursor.fetchall() #fetchone() vs fetchall() depending on the situation. We want all of the data here.
    except sqlite3.Error as error:
        print("Database error:", error)
    finally: #finally will always run after both a try and except. In other words: no matter if successful or not, this code will run.
        cursor.close()
    return products

#Create a user class to allow our login_manager to work properly
class User(UserMixin):
    def __init__(self, id, name, email, password):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

#Need to setup the login manager to enforce users having to login to be able to see certain pages.
@login_manager.user_loader
def load_user(user_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(id=user[0], name=user[1], email=user[2], password=user[3])
    return None
      
#Function accessing weather API at https://www.weatherapi.com/
def get_weather():
    try:
        API_KEY = 'a627aa23eb5e4fd3954133600242102'
        LOCATION = 'Horsham'
        response = requests.get(f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={LOCATION}&aqi=no')
        response.raise_for_status() #Will generate an error if there is a problem with our API call.

        json = response.json()

        weather_data = { #Extract the data from the JSON we received into a dictionary so we can use it later.
            'location': json['location']['name'],
            'temperature': json['current']['temp_c'],
            'condition': json['current']['condition'],
            'wind': json['current']['wind_mph']
        }

        return weather_data

    except requests.RequestException as err:
        return {'error fetching weather': str(err)}
    
@app.route('/home')
@login_required #This will not allow a user to navigate to this page unless they are logged in.
def home():
    date, time = getCurrentDateTime()
    return render_template('home.html', date = date, time = time)

@app.route('/about')
def about():
    return render_template('about.html')

#Login page and handling login POST
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    #When the user submits (or rather POSTs) we run the following code.
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM users WHERE email='{username}'")
            user = cursor.fetchone() #fetchone() vs fetchall() depending on the situation. We only want to find 1 user here.
        except sqlite3.Error as error:
            print("Database error:", error)
            flash('Database error')
            return render_template('login.html')
        finally: #finally will always run after both a try AND except.
            cursor.close() 

        if user: #if username is found          
            #Check if password entered on login page matches DB password against that username.
            if check_password_hash(user[3], password): #[3] is the password field.
                login_user(User(id=user[0], name=user[1], email=user[2], password=user[3]))
                flash('Logged in successfully.')
                return redirect(url_for('home')) #Redirect to the homepage on correct credentials
            else: #incorrect password
                flash('Invalid username or password')
                return render_template('login.html') #Return to login page if not a match (you probably want to display an error message here!)
        else: #username is not found
            flash('Invalid username or password')
            return render_template('login.html')
    else:     
        return render_template('login.html') #Just load the login page on a GET request.

#Signup page and handling signup POST
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    #When the user submits (or rather POSTs) the form we run the following code.
    if request.method == 'POST':
        fName = request.form['fname'] #Assign the form contents to variables for us to use later.
        sName = request.form['sname']        
        email = request.form['email']
        password = request.form['password']

        name = fName + " " + sName

        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM users WHERE email='{email}'")
            user = cursor.fetchone()
        except sqlite3.Error as error:
            print("Database error:", error)
            flash('Database error')
        finally: 
            cursor.close()

        if user: #Checks if there is already a user with this email address.
            flash('Email already registered')
            return redirect(url_for('signup')) #You should provide some feedback to the user rather than just redirect to the same page like this.
        else:
            try:
                query = "INSERT INTO users VALUES (NULL, ?, ?, ?)" # Use NULL for the ID value, SQLite will generate it for you.
                insert_data = (name, email, generate_password_hash(password)) #Create a tuple with all the data we want to INSERT.
                cursor = connection.cursor()
                cursor.execute(query, insert_data) #Combine the query with the data to insert + execute.
                connection.commit() #This is necessary to permanently make the change to our DB, the change will not persist without it.
            except sqlite3.Error as error:
                print("Database error:", error)
                flash('Database error')
                return render_template('signup.html')
            finally: 
                cursor.close()
     
            flash('Registration successful')
            return redirect(url_for('login')) #Successful signup - return to login page
    else:
        return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html')

@app.route('/products')
@login_required
def products():
    return render_template('products.html', products = getProducts())

@app.route('/weather')
def weather():
    return render_template('weather.html', weather_data = get_weather())

#Run in debug mode.
if __name__ == '__main__':
    app.run(debug = True)