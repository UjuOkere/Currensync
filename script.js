// Save preferences
function savePreferences() {
  localStorage.setItem('fromCurrency', document.getElementById('fromCurrency').value);
  localStorage.setItem('toCurrency', document.getElementById('toCurrency').value);
  localStorage.setItem('amount', document.getElementById('amount').value);
}

// Load preferences
function loadPreferences() {
  const from = localStorage.getItem('fromCurrency');
  const to = localStorage.getItem('toCurrency');
  const amount = localStorage.getItem('amount');

  if (from) document.getElementById('fromCurrency').value = from;
  if (to) document.getElementById('toCurrency').value = to;
  if (amount) document.getElementById('amount').value = amount;
}

// Conversion function
async function convertCurrency() {
  const amount = parseFloat(document.getElementById('amount').value);
  const from = document.getElementById('fromCurrency').value;
  const to = document.getElementById('toCurrency').value;

  if (isNaN(amount)) {
    document.getElementById('result').innerText = "Please enter a valid amount.";
    return;
  }

  try {
    const res = await fetch(`https://api.exchangerate-api.com/v4/latest/${from}`);
    const data = await res.json();
    const rate = data.rates[to];
    const converted = (amount * rate).toFixed(2);

    document.getElementById('result').innerText = `${amount} ${from} = ${converted} ${to}`;
    savePreferences(); // Save selection after conversion
  } catch (err) {
    document.getElementById('result').innerText = "Failed to fetch exchange rate.";
  }
}

// Load preferences when the page loads
window.onload = loadPreferences;
