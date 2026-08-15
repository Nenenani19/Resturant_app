import streamlit as st
import os
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, create_user, get_user_by_username

# Initialize database
init_db()

st.set_page_config(page_title="Restaurant App", layout="wide")

if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'user' not in st.session_state:
    st.session_state.user = None

# Helper functions

def add_to_cart(item, quantity=1):
    existing = next((x for x in st.session_state.cart if x['id'] == item['id']), None)
    if existing:
        existing['quantity'] += quantity
    else:
        st.session_state.cart.append({'id': item['id'], 'name': item['name'], 'price': item['price'], 'quantity': quantity})


def remove_from_cart(item_id):
    st.session_state.cart = [x for x in st.session_state.cart if x['id'] != item_id]


def update_quantity(item_id, quantity):
    for it in st.session_state.cart:
        if it['id'] == item_id:
            it['quantity'] = quantity


# UI
menu = st.sidebar.selectbox('Navigate', ['Home', 'Menu', 'Cart', 'Login / Signup', 'Profile', 'Orders'])

st.title("Restaurant Ordering")

if menu == 'Home':
    st.write("Welcome to the Restaurant app. Use the sidebar to navigate.")

elif menu == 'Menu':
    st.header('Menu')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY id')
        categories = cursor.fetchall()
        for cat in categories:
            st.subheader(cat['name'])
            cursor.execute('SELECT * FROM menu_items WHERE category_id = ? AND available = 1 ORDER BY name', (cat['id'],))
            items = cursor.fetchall()
            cols = st.columns(3)
            for i, item in enumerate(items):
                col = cols[i % 3]
                with col:
                    st.markdown(f"**{item['name']}**")
                    st.write(item['description'] or '')
                    st.write(f"Price: ${item['price']:.2f}")
                    qty = st.number_input(f"Qty_{item['id']}", min_value=1, value=1, key=f"qty_{item['id']}")
                    if st.button('Add to cart', key=f"add_{item['id']}"):
                        add_to_cart(item, int(qty))
                        st.success(f"Added {int(qty)} x {item['name']} to cart")

elif menu == 'Cart':
    st.header('Your Cart')
    cart = st.session_state.cart
    if not cart:
        st.info('Cart is empty')
    else:
        for it in cart:
            cols = st.columns([4,1,1,1])
            cols[0].write(it['name'])
            new_qty = cols[1].number_input(f"cart_qty_{it['id']}", min_value=1, value=it['quantity'], key=f"cart_qty_{it['id']}")
            if new_qty != it['quantity']:
                update_quantity(it['id'], int(new_qty))
                st.experimental_rerun()
            cols[2].write(f"${it['price']:.2f}")
            if cols[3].button('Remove', key=f"remove_{it['id']}"):
                remove_from_cart(it['id'])
                st.experimental_rerun()

        total = sum(x['price'] * x['quantity'] for x in cart)
        st.markdown(f"**Total: ${total:.2f}**")

        st.subheader('Place Order')
        with st.form('place_order'):
            name = st.text_input('Name')
            phone = st.text_input('Phone')
            address = st.text_area('Address')
            submitted = st.form_submit_button('Place order')
            if submitted:
                if not cart:
                    st.error('Cart is empty')
                elif not name or not phone:
                    st.error('Please provide name and phone')
                else:
                    try:
                        with get_db() as conn:
                            cursor = conn.cursor()
                            total_amount = sum(item['price'] * item['quantity'] for item in cart)
                            cursor.execute('''
                                INSERT INTO orders (customer_name, customer_phone, customer_address, total_amount)
                                VALUES (?, ?, ?, ?)
                            ''', (name, phone, address, total_amount))
                            order_id = cursor.lastrowid
                            for item in cart:
                                cursor.execute('''
                                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                                    VALUES (?, ?, ?, ?)
                                ''', (order_id, item['id'], item['quantity'], item['price']))
                            st.success(f'Order placed successfully! Order ID: {order_id}')
                            st.session_state.cart = []
                    except Exception as e:
                        st.error(f'Error placing order: {e}')

elif menu == 'Login / Signup':
    st.header('Login')
    with st.form('login_form'):
        uname = st.text_input('Username')
        pwd = st.text_input('Password', type='password')
        login_sub = st.form_submit_button('Login')
        if login_sub:
            with get_db() as conn:
                cursor = conn.cursor()
                user = get_user_by_username(cursor, uname)
                if not user or not check_password_hash(user['password_hash'], pwd):
                    st.error('Invalid username or password')
                else:
                    st.session_state.user = {'id': user['id'], 'username': user['username']}
                    st.success('Logged in')

    st.header('Signup')
    with st.form('signup_form'):
        s_uname = st.text_input('New username')
        s_pwd = st.text_input('New password', type='password')
        s_email = st.text_input('Email')
        s_full = st.text_input('Full name')
        s_phone = st.text_input('Phone (optional)')
        s_addr = st.text_area('Address (optional)')
        signup_sub = st.form_submit_button('Sign up')
        if signup_sub:
            if not s_uname or not s_pwd or not s_email or not s_full:
                st.error('Please fill required fields')
            else:
                with get_db() as conn:
                    cursor = conn.cursor()
                    existing = get_user_by_username(cursor, s_uname)
                    if existing:
                        st.error('Username already taken')
                    else:
                        pw_hash = generate_password_hash(s_pwd)
                        user_id = create_user(cursor, s_uname, pw_hash, s_email, s_full, s_phone, s_addr)
                        st.success('Signup successful. You can now log in')

elif menu == 'Profile':
    st.header('Profile')
    if not st.session_state.user:
        st.info('You must log in to view or edit profile')
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            user = get_user_by_username(cursor, st.session_state.user['username'])
            if user:
                st.write(f"Username: {user['username']}")
                with st.form('profile_form'):
                    email = st.text_input('Email', value=user['email'])
                    full = st.text_input('Full name', value=user['full_name'])
                    phone = st.text_input('Phone', value=user['phone'] or '')
                    addr = st.text_area('Address', value=user['address'] or '')
                    prof_sub = st.form_submit_button('Update')
                    if prof_sub:
                        if not email or not full:
                            st.error('Email and full name required')
                        else:
                            cursor.execute('''
                                UPDATE users SET email = ?, full_name = ?, phone = ?, address = ? WHERE id = ?
                            ''', (email, full, phone, addr, user['id']))
                            st.success('Profile updated')
            else:
                st.error('User not found')

elif menu == 'Orders':
    st.header('Orders')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        orders = cursor.fetchall()
        for o in orders:
            with st.expander(f"Order {o['id']} - {o['customer_name']} - ${o['total_amount']:.2f}"):
                st.write(f"Status: {o['status']}")
                st.write(f"Phone: {o['customer_phone']}")
                st.write(f"Address: {o['customer_address']}")
                cursor.execute('SELECT oi.*, m.name as item_name FROM order_items oi JOIN menu_items m ON oi.menu_item_id = m.id WHERE oi.order_id = ?', (o['id'],))
                items = cursor.fetchall()
                for it in items:
                    st.write(f"{it['quantity']} x {it['item_name']} @ ${it['price']:.2f}")
