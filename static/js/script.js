// Update cart count in navbar
function updateCartCount() {
    fetch('/api/cart')
        .then(response => response.json())
        .then(cart => {
            const count = cart.reduce((sum, item) => sum + item.quantity, 0);
            const badges = document.querySelectorAll('#cart-count');
            badges.forEach(badge => {
                badge.textContent = count;
            });
        })
        .catch(error => console.error('Error updating cart count:', error));
}

// Initialize cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
});