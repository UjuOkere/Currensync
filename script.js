async function convertCurrency() {
  const amount = document.getElementById('amount').value;
  const toCurrency = document.getElementById('currency').value;

  const res = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
  const data = await res.json();
  const rate = data.rates[toCurrency];
  const result = (amount * rate).toFixed(2);

  document.getElementById('result').innerText = `${amount} USD = ${result} ${toCurrency}`;
}

async function populateCurrencies() {
  const res = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
  const data = await res.json();
  const select = document.getElementById('currency');
  for (const currency in data.rates) {
    const option = document.createElement('option');
    option.value = currency;
    option.text = currency;
    select.appendChild(option);
  }
}
populateCurrencies();