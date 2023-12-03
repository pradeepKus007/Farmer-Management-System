from flask import Flask, render_template, request, redirect, url_for,session
import pymysql

app = Flask(__name__)
app.secret_key = '12345'

# Database Configuration
db = pymysql.connect(host='localhost', user='root', password='', database='Market')
cursor = db.cursor()

# User Registration######################################################################################################
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role=request.form['role']
        # Insert the user into the 'user' table
        cursor.execute("INSERT INTO user (name, email, password,role) VALUES (%s, %s, %s,%s)", (name, email, password,role))
        db.commit()

        # Determine if the user is a customer or a farmer (You can add radio buttons in the registration form)
        role = request.form['role']

        if role == 'customer':
            # Insert customer-specific data into the 'customer' table
            cursor.execute("INSERT INTO customer (user_id, shipping_address, billing_address) VALUES (%s, %s, %s)",
                           (cursor.lastrowid, request.form['shipping_address'], request.form['billing_address']))
        elif role == 'farmer':
            # Insert farmer-specific data into the 'farmer' table
            cursor.execute("INSERT INTO farmer (user_id, farm_name, address) VALUES (%s, %s, %s)",
                           (cursor.lastrowid, request.form['farm_name'], request.form['address']))

        db.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')
#################################################################################################################################################

# User Login########################################################################################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[2]
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"

    return render_template('login.html')
#################################################################################################################################################

# User Dashboard#################################################################################################################################################
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']
        
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id))
        user = cursor.fetchone()
        if user:
            name = user[1]
            role = user[4]
            shipping_address = None
            billing_address = None
            farm_name = None
            farm_address = None

            if role == 'Customer':
                cursor.execute("SELECT * FROM customer WHERE user_id = %s", (user_id))
                customer_data = cursor.fetchone()
                if customer_data:
                    shipping_address = customer_data[2]
                    billing_address = customer_data[3]

            elif role == 'Farmer':
                cursor.execute("SELECT * FROM farmer WHERE user_id = %s", (user_id))
                farmer_data = cursor.fetchone()
                if farmer_data:
                    farm_name = farmer_data[2]
                    farm_address = farmer_data[3]

            return render_template('home.html', name=name, role=role, shipping_address=shipping_address, billing_address=billing_address, farm_name=farm_name, farm_address=farm_address)
        else:
            return "User not found"
   

#################################################################################################################################################



#################################################################################################################################################
@app.route('/post_product', methods=['GET', 'POST'])
def post_product():
    if 'user_id' in session:
        if request.method == 'POST':
            user_id = session['user_id']
            cursor.execute("SELECT * FROM farmer WHERE user_id = %s", (user_id,))
            farmer_data = cursor.fetchone()
            if farmer_data:
                farmer_id= farmer_data[0]
                name = request.form.get('name')
                description = request.form.get('description')
                price = request.form.get('price')
                # Insert the product data into the 'product' table
                cursor.execute("INSERT INTO product (farmer_id, name, description, price) VALUES (%s, %s, %s, %s)",(farmer_id, name, description, price))
                db.commit()  # Commit the changes to the database
                # Redirect to a success page or the home page
                return redirect(url_for('home'))

        return render_template('post.html')  # Create a post product form or page
    else:
        return "User not logged in"

#################################################################################################################################################


#################################################################################################################################################
@app.route('/products')
def products():
    if 'user_id' in session:
        user_id = session['user_id']
    # Retrieve a list of products from the database
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id))
    user_data = cursor.fetchone()
    user_role=user_data[4]
    if user_role=="Farmer":
        cursor.execute("SELECT * FROM farmer WHERE user_id = %s", (user_id))
        farmer_data = cursor.fetchone()
        farmer_id=farmer_data[0]
        return render_template('product.html', products=products,farmer_id=farmer_id)
    elif user_role=="Customer":
        return render_template('product.html', products=products,user_role=user_role)


#################################################################################################################################################
#################################################################################################################################################

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' in session:
        user_id = session['user_id']
        # Check if the logged-in user is the owner of the product
        cursor.execute("SELECT farmer_id FROM product WHERE product_id = %s", (product_id,))
        owner_id = cursor.fetchone()
        cursor.execute("SELECT farmer_id FROM farmer WHERE user_id = %s", (user_id,))
        loginUser_id = cursor.fetchone()

        if owner_id == loginUser_id:
            # Delete the product from the database
            cursor.execute("DELETE FROM product WHERE product_id = %s", (product_id,))
            db.commit()
            return redirect(url_for('products'))
        else:
            return "You don't have permission to delete this product."
    else:
        return "You must be logged in to delete this product."


#################################################################################################################################################

#################################################################################################################################################
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if request.method == 'GET':
        # Retrieve the product details from the database
        cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product:
            return render_template('edit_product.html', product=product)
        else:
            return "Product not found"

    elif request.method == 'POST':
        # Handle the form submission to update the product details in the database
        # Retrieve form data (e.g., new name, description, and price)
        new_name = request.form.get('new_name')
        new_description = request.form.get('new_description')
        new_price = request.form.get('new_price')

        # Update the product in the database
        cursor.execute("UPDATE product SET name = %s, description = %s, price = %s WHERE product_id = %s",
                       (new_name, new_description, new_price, product_id))
        db.commit()
        return redirect(url_for('products'))
    

#########################################################################################################

@app.route('/add_comment/<int:product_id>', methods=['GET', 'POST'])
def add_comment(product_id):
    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']

        # Retrieve the role of the user from the database
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()

        cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
        product_data = cursor.fetchone()

        cursor.execute("SELECT * FROM customer WHERE user_id = %s", (user_id,))
        customer_data = cursor.fetchone()

        if user_data[4] == 'Customer':
            # Get the comment from the form
            if request.method == 'POST':
                comment = request.form.get('comment')

                # Insert the comment into the 'review' table
                cursor.execute("INSERT INTO review (product_id, customer_id, comment) VALUES (%s, %s, %s)",
                               (product_id, customer_data[0], comment))
                db.commit()

                # Redirect to a success page or the product details page
                return redirect(url_for('products', product_id=product_id, customer_id=customer_data[0]))
            else:
                previous_comments = fetch_previous_comments(product_id)
                return render_template('add_comment.html', product_id=product_id,pro_name=product_data[2],all_com=previous_comments)
        else:
            return "You can't add comments."
    else:
        return "You must be logged in to add a comment."


def fetch_previous_comments(product_id):
    # Assuming you have a database connection and cursor set up
    cursor.execute("""
    SELECT r.review_id, u.name, r.comment
    FROM review r
    JOIN customer c ON r.customer_id = c.customer_id
    JOIN user u ON c.user_id = u.user_id
    WHERE r.product_id = %s
""", (product_id,))

    comments = cursor.fetchall()
    return comments

###############################################################################################
# Define a route to add educational resources (for farmers only)
@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
        user_role = cursor.fetchone()

        if user_role[0] == 'Farmer':
            if request.method == 'POST':
                title = request.form.get('title')
                description = request.form.get('description')
                url = request.form.get('url')

                # Get the farmer_id based on the user_id
                cursor.execute("SELECT farmer_id FROM farmer WHERE user_id = %s", (user_id,))
                farmer_id = cursor.fetchone()

                if farmer_id:
                    # Insert the educational resource into the table
                    cursor.execute('''
                        INSERT INTO educational_resource (farmer_id, title, description, url)
                        VALUES (%s, %s, %s, %s)
                    ''', (farmer_id[0], title, description, url))
                    db.commit()

                    # Redirect to a success page or the educational resources page
                    return redirect(url_for('home'))
                else:
                    return "Farmer not found"
            
            return render_template('add_resource.html')
        else:
            return "You must be a farmer to add educational resources."
    else:
        return "You must be logged in to add educational resources."


# Define a route to view educational resources
@app.route('/educational_resources')
def educational_resources():
    if 'user_id' in session:
        user_id = session['user_id']
    cursor.execute('SELECT * FROM educational_resource')
    resources = cursor.fetchall()

    cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id))
    user_data = cursor.fetchone()

    user_role=user_data[4]
    if user_role=="Farmer":
        cursor.execute("SELECT * FROM farmer WHERE user_id = %s", (user_id))
        farmer_data = cursor.fetchone()
        farmer_id=farmer_data[0]
        return render_template('educational_resources.html', resources=resources,farmer_id=farmer_id)
    elif user_role=="Customer":
        return render_template('educational_resources.html', resources=resources,user_role=user_role)


################################################################################################################


# Define a route to edit an educational resource (for farmers only)
@app.route('/edit_resource/<int:educational_resource_id>', methods=['GET', 'POST'])
def edit_resource(educational_resource_id):
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
        user_role = cursor.fetchone()

        if user_role[0] == 'Farmer':
            if request.method == 'POST':
                title = request.form.get('title')
                description = request.form.get('description')
                url = request.form.get('url')

                # Update the educational resource in the table
                cursor.execute('''
                    UPDATE educational_resource
                    SET title = %s, description = %s, url = %s
                    WHERE educational_resource_id = %s
                ''', (title, description, url, educational_resource_id))
                db.commit()

                # Redirect to the educational resources page
                return redirect(url_for('educational_resources'))

            # Load the existing resource data for editing
            cursor.execute('''
                SELECT educational_resource_id, title, description, url
                FROM educational_resource
                WHERE educational_resource_id = %s
            ''', (educational_resource_id,))
            resource = cursor.fetchone()

            return render_template('edit_resource.html', resource=resource)
        else:
            return "You must be a farmer to edit educational resources."
    else:
        return "You must be logged in to edit educational resources."
##########################################################################################################################
    

@app.route('/delete_resource/<int:educational_resource_id>', methods=['GET', 'POST'])
def delete_resource(educational_resource_id):
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT farmer_id FROM educational_resource WHERE educational_resource_id = %s", (educational_resource_id,))
        farmer_id = cursor.fetchone()
        cursor.execute("SELECT farmer_id FROM farmer WHERE user_id = %s", (user_id,))
        loginUser_id = cursor.fetchone()
        if  farmer_id == loginUser_id:
            # Perform the resource deletion
            cursor.execute("DELETE FROM educational_resource WHERE educational_resource_id = %s", (educational_resource_id,))
            db.commit()

            # Redirect to the educational resources page
            return redirect(url_for('educational_resources'))
        else:
            return "You must be a farmer to delete educational resources."
    else:
        return "You must be logged in to delete educational resources."


   ###################################################################################################################################################################
@app.route('/add_to_cart', methods=['GET'])
def add_to_cart():
    if 'user_id' in session:
        user_id = session['user_id']

        
        
        # Get the product_id from the query parameters
        product_id = request.args.get('product_id')

        if product_id is not None:
            cursor = db.cursor()

            # Check if the product exists
            cursor.execute("SELECT * FROM product WHERE product_id = %s", (product_id,))
            product = cursor.fetchone()

            # Check if the product exists
            cursor.execute("SELECT * FROM customer WHERE user_id = %s", (user_id,))
            customer_id = cursor.fetchone()

            if product:
                # Check if the product is already in the cart
                cursor.execute("SELECT * FROM cart WHERE customer_id = %s AND product_id = %s", (customer_id[0], product_id))
                existing_cart_item = cursor.fetchone()

                if existing_cart_item:
                    # If the product is already in the cart, update the quantity
                    new_quantity = existing_cart_item[3] + 1
                    cursor.execute("UPDATE cart SET quantity = %s WHERE customer_id = %s AND product_id = %s", (new_quantity, customer_id[0], product_id))
                else:
                    # If the product is not in the cart, insert a new cart item
                    cursor.execute("INSERT INTO cart (customer_id, product_id, quantity) VALUES (%s, %s, 1)", (customer_id[0], product_id))

                # Commit the changes to the database
                db.commit()
                
                # Redirect to a page, for example, the product list page
                return redirect(url_for('products'))
            else:
                return "Product not found."

    return "You must be logged in as a customer to add products to your cart."

######################################################################################################

@app.route('/view_cart')
def view_cart():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
        user_role = cursor.fetchone()[0]

        if user_role == "Customer":
            cursor.execute("SELECT customer_id FROM customer WHERE user_id = %s", (user_id,))
            customer_id = cursor.fetchone()[0]

            # Fetch the cart items for the current customer
            cursor.execute("SELECT c.product_id, p.name, p.price, c.quantity FROM cart c JOIN product p ON c.product_id = p.product_id WHERE c.customer_id = %s", (customer_id,))
            cart_items = cursor.fetchall()

            return render_template('view_cart.html', cart_items=cart_items)

    return "You must be logged in as a customer to view your cart."
#####################################################################################################

from datetime import datetime
from decimal import Decimal

@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
        user_role = cursor.fetchone()[0]

        if user_role == "Customer":
            cursor.execute("SELECT customer_id FROM customer WHERE user_id = %s", (user_id,))
            customer_id = cursor.fetchone()[0]

            # Get the items in the customer's cart
            cursor.execute("SELECT * FROM cart WHERE customer_id = %s", (customer_id,))
            cart_items = cursor.fetchall()
            try:
                # Start the transaction
                db.begin()

                # Calculate the total amount
                total_amount = Decimal(0)
                for item in cart_items:
                    cursor.execute("SELECT price FROM product WHERE product_id = %s", (item[2],))
                    price = cursor.fetchone()[0]
                    total_amount += item[3] * price

                # Create a new transaction record
                cursor.execute("INSERT INTO transaction (customer_id,product_id, date, total_amount) VALUES (%s,%s, NOW(), %s)",
                               (customer_id, item[2],total_amount))

                 # Get the transaction_id of the newly inserted record
                transaction_id = cursor.lastrowid

                # Insert individual items into the transaction_products table
                for item in cart_items:
                    cursor.execute("INSERT INTO purchase (transaction_id, product_id, quantity) VALUES (%s, %s, %s)",
                                   (transaction_id, item[2], item[3]))

                # Mark the cart items as purchased or remove them from the cart
                for item in cart_items:
                    cursor.execute("DELETE FROM cart WHERE cart_id = %s", (item[0],))

                # Commit the transaction if everything is successful
                db.commit()

                return redirect(url_for('home'))
            except Exception as e:
                # Rollback the transaction in case of an error
                db.rollback()
                print(f"Transaction failed: {str(e)}")
                return "Transaction failed. Please try again."

    return "You must be logged in as a customer to perform checkout."




################################################################################
@app.route('/view_transaction', methods=['GET'])
def view_transaction():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT role FROM user WHERE user_id = %s", (user_id,))
        user_role = cursor.fetchone()[0]

        if user_role == "Customer":
            cursor.execute("SELECT customer_id FROM customer WHERE user_id = %s", (user_id,))
            customer_id = cursor.fetchone()[0]

            # Fetch the transaction details for the last transaction
            cursor.execute("SELECT * FROM transaction WHERE customer_id = %s ORDER BY date DESC", (customer_id))
            transaction_items = cursor.fetchall()

            if not transaction_items:
                return "No transactions found."

            return render_template('checkout.html',transaction_items=transaction_items)

    return "You must be logged in as a customer to view this page."

###############################################################################

@app.route('/purchase_report', methods=['GET'])
def purchase_report():
    # Get the sorting preference from the form
    sort_date = request.args.get('sort_date', 'asc')

    # Modify the SQL query to include sorting
    cursor.execute("""
        SELECT
            user.name AS customer_name,
            transaction.transaction_id,
            customer.shipping_address,
            farmer.farm_name,
            product.name AS product_name,
            transaction.total_amount,
            transaction.date,
            purchase.quantity
        FROM
            user
        JOIN
            customer ON user.user_id = customer.user_id
        JOIN
            transaction ON customer.customer_id = transaction.customer_id
        LEFT JOIN
            purchase ON transaction.transaction_id = purchase.transaction_id
        LEFT JOIN
            product ON purchase.product_id = product.product_id
        LEFT JOIN
            farmer ON product.farmer_id = farmer.farmer_id
           WHERE
        transaction.date BETWEEN '2023-01-01' AND '2024-11-10'
    ORDER BY
        transaction.date """ + ("ASC" if sort_date == "asc" else "DESC") + 
    """
""")

    # Fetch all the results
    results = cursor.fetchall()

    # Render the template with the results and sorting preference
    return render_template('purchase_report.html', results=results, sort_date=sort_date)
    
#####################################################################################################




# Logout
@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# Define a route for the root URL
@app.route('/')
def index():
    return redirect(url_for('signup'))

if __name__ == '__main__':
    app.run(debug=True)
#################################################################################################################################################
