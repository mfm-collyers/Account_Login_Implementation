from flask import Flask, render_template #Flask library and functions
import sqlite3 #Our database
import datetime #Used to display current date & time

#Instantiate Flask App
app = Flask(__name__)

#Connection to DB
connection = sqlite3.connect('BeanBrew.db', check_same_thread=False) #Will create DB if it doesn't already exist

#Set up table if it doesn't exist already
query = """CREATE TABLE IF NOT EXISTS product(id INTEGER PRIMARY KEY, productName TEXT NOT NULL, productDescription TEXT NOT NULL, price REAL NOT NULL);"""
cursor = connection.cursor()
cursor.execute(query)
cursor.close() #Important to make sure we close the cursor when we are done with it.

def getCurrentDateTime():
    date = datetime.datetime.now().date()
    time = datetime.datetime.now().time()
    return date.strftime("%d/%m/%Y"), time.strftime("%X") #Format the date and time correctly before returning

def getProducts():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Product")
        products = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally: 
        cursor.close()
        
    print(products)
    return products

#Starting (index) page
@app.route('/')
@app.route('/home')
def home():
    date, time = getCurrentDateTime()
    return render_template('home.html', date = date, time = time)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/products')
def products():
    products = getProducts()
    return render_template('products.html', products = products)

#Run in debug mode.
if __name__ == '__main__':
    app.run(debug = True)