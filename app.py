import os

try:
    # Try to import Flask; if Flask isn't available (e.g., running on Streamlit Cloud), fall back
    from flask import Flask, render_template, request, jsonify, session, redirect, url_for
    from werkzeug.security import generate_password_hash, check_password_hash
    from database import get_db, init_db, create_user, get_user_by_username
    FLASK_AVAILABLE = True
except Exception:
    FLASK_AVAILABLE = False

if not FLASK_AVAILABLE:
    # When Flask is not installed, import the Streamlit entrypoint so Streamlit Cloud
    # can run the Streamlit app by importing this module (app.py). streamlit_app.py
    # contains the Streamlit UI and will execute on import.
    try:
        import streamlit_app  # noqa: F401
    except Exception:
        # If importing the Streamlit app fails, don't raise so the environment doesn't crash
        # The Streamlit runtime will show errors from streamlit_app when it runs directly.
        pass
else:
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # Initialize database when the app starts.
    init_db()

    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')

    @app.route('/menu')
    def menu():
        """Display menu items"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, c.name as category_name 
                FROM menu_items m
                JOIN categories c ON m.category_id = c.id
                WHERE m.available = 1
                ORDER BY c.id, m.name
            ''')
            items = cursor.fetchall()
            
            cursor.execute('SELECT * FROM categories ORDER BY id')
            categories = cursor.fetchall()
        
        return render_template('menu.html', items=items, categories=categories)

    @app.route('/api/menu')
    def api_menu():
        """API endpoint for menu items"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, c.name as category_name 
                FROM menu_items m
                JOIN categories c ON m.category_id = c.id
                WHERE m.available = 1
            ''')
            items = [dict(row) for row in cursor.fetchall()]
        return jsonify(items)

    @app.route('/api/cart', methods=['GET', 'POST'])
    def cart():
        """Handle cart operations"""
        if 'cart' not in session:
            session['cart'] = []
        
        if request.method == 'POST':
            data = request.json
            action = data.get('action')
            
            if action == 'add':
                item_id = data.get('item_id')
                quantity = data.get('quantity', 1)
                
                # Get item details
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,))
                    item = cursor.fetchone()
                
                if item:
                    cart_item = {
                        'id': item['id'],
                        'name': item['name'],
                        'price': item['price'],
                        'quantity': quantity
                    }
                    
                    # Check if item already in cart
                    existing = next((x for x in session['cart'] if x['id'] == item_id), None)
                    if existing:
                        existing['quantity'] += quantity
                    else:
                        session['cart'].append(cart_item)
                    
                    session.modified = True
                    return jsonify({'success': True, 'cart': session['cart']})
            
            elif action == 'remove':
                item_id = data.get('item_id')
                session['cart'] = [x for x in session['cart'] if x['id'] != item_id]
                session.modified = True
                return jsonify({'success': True, 'cart': session['cart']})
            
            elif action == 'update':
                item_id = data.get('item_id')
                quantity = data.get('quantity')
                for item in session['cart']:
                    if item['id'] == item_id:
                        item['quantity'] = quantity
                session.modified = True
                return jsonify({'success': True, 'cart': session['cart']})
            
            elif action == 'clear':
                session['cart'] = []
                session.modified = True
                return jsonify({'success': True, 'cart': []})
        
        return jsonify(session['cart'])

    @app.route('/cart')
    def cart_page():
        """Cart page"""
        cart = session.get('cart', [])
        total = sum(item['price'] * item['quantity'] for item in cart)
        return render_template('cart.html', cart=cart, total=total)


    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            address = request.form.get('address')

            if not all([username, password, email, full_name]):
                return render_template('signup.html', error='Please fill in all required fields')

            with get_db() as conn:
                cursor = conn.cursor()
                existing = get_user_by_username(cursor, username)
                if existing:
                    return render_template('signup.html', error='Username already taken')
                pw_hash = generate_password_hash(password)
                user_id = create_user(cursor, username, pw_hash, email, full_name, phone, address)

            # Log the user in
            session['user'] = {'id': user_id, 'username': username}
            session.modified = True
            return redirect(url_for('index'))

        return render_template('signup.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                return render_template('login.html', error='Please provide username and password')

            with get_db() as conn:
                cursor = conn.cursor()
                user = get_user_by_username(cursor, username)
                if not user:
                    return render_template('login.html', error='Invalid username or password')
                if not check_password_hash(user['password_hash'], password):
                    return render_template('login.html', error='Invalid username or password')

            # Successful login
            session['user'] = {'id': user['id'], 'username': user['username']}
            session.modified = True
            return redirect(url_for('index'))

        return render_template('login.html')


    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user' not in session:
            return redirect(url_for('login'))

        with get_db() as conn:
            cursor = conn.cursor()
            user = get_user_by_username(cursor, session['user']['username'])
            
            if request.method == 'POST':
                email = request.form.get('email')
                full_name = request.form.get('full_name')
                phone = request.form.get('phone')
                address = request.form.get('address')

                if not all([email, full_name]):
                    return render_template('profile.html', user=user, error='Email and full name are required')

                cursor.execute('''
                    UPDATE users 
                    SET email = ?, full_name = ?, phone = ?, address = ?
                    WHERE id = ?
                ''', (email, full_name, phone, address, user['id']))
                
                # Refresh user data
                user = get_user_by_username(cursor, session['user']['username'])
                return render_template('profile.html', user=user, success='Profile updated successfully')

        return render_template('profile.html', user=user)

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        session.modified = True
        return redirect(url_for('index'))

    @app.route('/api/order', methods=['POST'])
    def create_order():
        """Create new order"""
        data = request.json
        cart = session.get('cart', [])
        
        if not cart:
            return jsonify({'success': False, 'message': 'Cart is empty'})
        
        customer_name = data.get('name')
        customer_phone = data.get('phone')
        customer_address = data.get('address')
        
        if not all([customer_name, customer_phone]):
            return jsonify({'success': False, 'message': 'Missing customer information'})
        
        total_amount = sum(item['price'] * item['quantity'] for item in cart)
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Insert order
                cursor.execute('''
                    INSERT INTO orders (customer_name, customer_phone, customer_address, total_amount)
                    VALUES (?, ?, ?, ?)
                ''', (customer_name, customer_phone, customer_address, total_amount))
                
                order_id = cursor.lastrowid
                
                # Insert order items
                for item in cart:
                    cursor.execute('''
                        INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    ''', (order_id, item['id'], item['quantity'], item['price']))
                
                # Clear cart
                session['cart'] = []
                session.modified = True
                
                return jsonify({
                    'success': True, 
                    'message': 'Order placed successfully!',
                    'order_id': order_id
                })
        
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/orders')
    def orders():
        """View all orders"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders 
                ORDER BY created_at DESC
            ''')
            orders_list = cursor.fetchall()
        
        return render_template('orders.html', orders=orders_list)

    @app.route('/api/order/<int:order_id>')
    def get_order(order_id):
        """Get order details"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            order = cursor.fetchone()
            
            cursor.execute('''
                SELECT oi.*, m.name as item_name
                FROM order_items oi
                JOIN menu_items m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
            ''', (order_id,))
            items = cursor.fetchall()
        
        if order:
            return jsonify({
                'order': dict(order),
                'items': [dict(item) for item in items]
            })
        return jsonify({'error': 'Order not found'}), 404

    @app.route('/api/order/<int:order_id>/status', methods=['PUT'])
    def update_order_status(order_id):
        """Update order status"""
        data = request.json
        status = data.get('status')
        
        valid_statuses = ['pending', 'preparing', 'ready', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        
        return jsonify({'success': True, 'message': 'Status updated'})

    if __name__ == '__main__':
        app.run(debug=True, port=5000)
