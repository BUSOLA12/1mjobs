async function updateInvoiceContent() {
  try {
    // Get order ID from URL
    const urlParts = window.location.pathname.split('/');
    const orderId = urlParts[urlParts.length - 1] || urlParts[urlParts.length - 2];
    if (!/^\d+$/.test(orderId)) {
      throw new Error('Invalid order ID in URL');
    }

    // Fetch user details
    const userRes = await fetchProtected('/api/users/me/', {
      headers: { 'Content-Type': 'application/json' }
    });
    if (!userRes.ok) {
        const errorData = await userRes.json();
        console.log(errorData);
    }
    const userData = await userRes.json();

    // Fetch order details
    const orderRes = await fetchProtected(`/api/pricing/orders/${orderId}/`, {
    });
    if (!orderRes.ok){
        const errorData = await orderRes.json();
        console.log(errorData);
    }
    const orderData = await orderRes.json();

    // --- Update Customer Info ---
    const customerName = userData.user.first_name + " " + userData.user.last_name;
    const customerHTML = `
      ${customerName != ' '? customerName : userData.user.email|| 'User'} <br>
      ${capitalize(userData.user.role) || ''} <br>
      
    `;
    document.getElementById('customer-info').innerHTML = customerHTML;

    // --- Update Order Info ---
    const issuedDate = new Date(orderData.created_at);
    const dueDate = new Date(issuedDate);
    dueDate.setDate(issuedDate.getDate() + 7);
    const issuedFormatted = issuedDate.toISOString().split('T')[0];
    const orderDetailsHTML = `
      <strong>Order:</strong> #${orderData.id} <br>
      <strong>Issued:</strong> ${issuedFormatted} <br>
      Due 7 days from date of issue
    `;
    document.getElementById('details').innerHTML = orderDetailsHTML;

    // --- Update Invoice Table ---
    const planDescription = capitalize(orderData.plan_data?.description) || 'Plan';
    const amount = parseFloat(orderData.amount);
    const vat = (amount * 0.2);
    const total = (parseFloat(amount) + parseFloat(vat));

    const invoiceRow = `
      <tr>
        <td>${planDescription}</td>
        <td>₦${amount.toLocaleString('en-NG')}</td>
        <td>₦${vat.toLocaleString('en-NG')}</td>
        <td>₦${total.toLocaleString('en-NG')}</td>
      </tr>
    `;
    const invoiceTable = document.querySelector('table.margin-top-20');
    invoiceTable.innerHTML = `
      <tr>
        <th>Description</th>
        <th>Price</th>
        <th>VAT (20%)</th>
        <th>Total</th>
      </tr>
      ${invoiceRow}
    `;

    // --- Update Total Due ---
    const totalsTable = document.getElementById('totals');
    totalsTable.innerHTML = `
      <tr>
        <th>Total Due</th> 
        <th><span>₦${total.toLocaleString('en-NG')}</span></th>
      </tr>
    `;

    hideLoading();

  } catch (error) {
    console.error('Invoice load error:', error);
  }
}

// Run when DOM is loaded
document.addEventListener('DOMContentLoaded', updateInvoiceContent);