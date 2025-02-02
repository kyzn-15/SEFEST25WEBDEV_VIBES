function validateForm(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    // Simple validation example
    if (username === 'admin' && password === 'admin123') {
        alert('Login successful!');
        window.location.href = '#';
        return true;
    } else {
        errorMessage.style.display = 'block';
        return false;
    }
}
