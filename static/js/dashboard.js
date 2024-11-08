document.addEventListener('DOMContentLoaded', function() {
    const deliveryDate = document.getElementById('deliveryDate');
    const dailyDriverExpense = document.getElementById('dailyDriverExpense');

    // Create alert container
    const container = document.querySelector('.container');
    const alertContainer = document.createElement('div');
    alertContainer.className = 'alert-container mb-3';
    container.insertBefore(alertContainer, container.firstChild);
    
    const ordersTable = $('#ordersTable').DataTable({
        columns: [
            { data: 'customer_name' },
            { 
                data: 'total_cases',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cases-input" 
                               value="${data || 0}" min="0" style="width: 80px">`;
                    }
                    return data || 0;
                }
            },
            { 
                data: 'total_cost',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cost-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_cash',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input cash-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_check',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input check-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_credit',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input credit-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            {
                data: 'payment_received',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            }
        ],
        createdRow: function(row, data) {
            if (!data.isEditable) {
                $(row).addClass('text-muted');
            }
        },
        language: {
            emptyTable: "No orders found for the selected date",
            loadingRecords: "Loading orders...",
            zeroRecords: "No matching orders found",
            error: "Error loading order data"
        },
        processing: true,
        serverSide: false,
        dom: '<"row"<"col-md-12"f>>rt<"row"<"col-md-6"l><"col-md-6"p>>'
    });

    // Initialize date picker with today's date
    deliveryDate.valueAsDate = new Date();
    loadOrders();

    // Show/hide Add Order button based on selected date
    function updateAddOrderButton() {
        const today = new Date().toISOString().split('T')[0];
        const addOrderBtn = document.getElementById('addOrderBtn');
        if (addOrderBtn) {
            addOrderBtn.style.display = deliveryDate.value === today ? 'block' : 'none';
        }
    }

    // Event Listeners
    deliveryDate.addEventListener('change', () => {
        loadOrders();
        loadDailyDriverExpense();
        updateAddOrderButton();
    });

    document.getElementById('saveDriverExpense').addEventListener('click', saveDailyDriverExpense);

    // Event delegation for input changes in the table
    $('#ordersTable').on('change', 'input', function() {
        const row = $(this).closest('tr');
        const data = ordersTable.row(row).data();
        if (!data) {
            showError('Error: Could not find order data');
            return;
        }
        const updatedData = collectRowData(row, data);
        updateOrder(data.id, updatedData);
    });

    async function updateOrder(orderId, updatedData) {
        try {
            if (!orderId) throw new Error('Invalid order ID');
            
            const response = await fetch(`/api/orders/${orderId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedData)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to update order');
            }

            await loadOrders();
            showSuccess('Order updated successfully');
        } catch (error) {
            console.error('Error updating order:', error);
            showError(`Failed to update order: ${error.message}`);
        }
    }

    async function loadCustomers() {
        try {
            const response = await fetch('/api/customers');
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to load customers');
            }
            
            const customers = await response.json();
            if (!Array.isArray(customers)) {
                throw new Error('Invalid customer data received');
            }
            
            const customerSelect = document.getElementById('customerId');
            customerSelect.innerHTML = customers.map(c => 
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
            
        } catch (error) {
            console.error('Error loading customers:', error);
            showError('Failed to load customers: ' + error.message);
        }
    }

    function collectRowData(row, originalData) {
        const data = {
            id: originalData.id,
            total_cases: parseInt(row.find('.cases-input').val()) || 0,
            total_cost: parseFloat(row.find('.cost-input').val()) || 0,
            payment_cash: parseFloat(row.find('.cash-input').val()) || 0,
            payment_check: parseFloat(row.find('.check-input').val()) || 0,
            payment_credit: parseFloat(row.find('.credit-input').val()) || 0
        };

        // Validate data
        if (data.total_cost < 0) throw new Error('Total cost cannot be negative');
        if (data.total_cases < 0) throw new Error('Cases cannot be negative');
        if (data.payment_cash < 0 || data.payment_check < 0 || data.payment_credit < 0) {
            throw new Error('Payments cannot be negative');
        }

        return data;
    }

    document.getElementById('saveOrder').addEventListener('click', async function() {
        try {
            const customerId = document.getElementById('customerId').value;
            if (!customerId) {
                throw new Error('Please select a customer');
            }

            const orderData = {
                customer_id: customerId,
                delivery_date: deliveryDate.value
            };

            const response = await fetch('/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to create order');
            }

            $('#orderModal').modal('hide');
            await loadOrders();
            showSuccess('Order created successfully');
        } catch (error) {
            console.error('Error saving order:', error);
            showError('Failed to create order: ' + error.message);
        }
    });

    async function loadOrders() {
        try {
            if (!deliveryDate.value) {
                throw new Error('Invalid date selected');
            }

            const response = await fetch(`/api/orders/${deliveryDate.value}`);
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to load orders');
            }

            const data = await response.json();
            if (!Array.isArray(data)) {
                throw new Error('Invalid order data received');
            }

            const today = new Date().toISOString().split('T')[0];
            const processedData = data.map(order => ({
                ...order,
                total_cases: parseInt(order.total_cases) || 0,
                total_cost: parseFloat(order.total_cost) || 0,
                payment_cash: parseFloat(order.payment_cash) || 0,
                payment_check: parseFloat(order.payment_check) || 0,
                payment_credit: parseFloat(order.payment_credit) || 0,
                payment_received: parseFloat(order.payment_received) || 0,
                isEditable: deliveryDate.value === today
            }));
            
            ordersTable.clear().rows.add(processedData).draw();
            updateTotals(processedData);
        } catch (error) {
            console.error('Error loading orders:', error);
            showError('Failed to load orders: ' + error.message);
            ordersTable.clear().draw();
        }
    }

    async function loadDailyDriverExpense() {
        try {
            if (!deliveryDate.value) {
                throw new Error('Invalid date selected');
            }

            const response = await fetch(`/api/daily_driver_expense/${deliveryDate.value}`);
            if (!response.ok && response.status !== 404) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to load driver expense');
            }

            if (response.status === 404) {
                dailyDriverExpense.value = 0;
                return;
            }

            const data = await response.json();
            if (typeof data.amount !== 'number') {
                throw new Error('Invalid driver expense data received');
            }

            dailyDriverExpense.value = data.amount || 0;
            updateTotals(ordersTable.data());
        } catch (error) {
            console.error('Error loading driver expense:', error);
            dailyDriverExpense.value = 0;
            showError('Failed to load driver expense: ' + error.message);
        }
    }

    async function saveDailyDriverExpense() {
        try {
            const amount = parseFloat(dailyDriverExpense.value);
            if (isNaN(amount) || amount < 0) {
                throw new Error('Invalid expense amount');
            }

            const response = await fetch('/api/daily_driver_expense', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: deliveryDate.value,
                    amount: amount
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to save driver expense');
            }

            updateTotals(ordersTable.data());
            showSuccess('Driver expense saved successfully');
        } catch (error) {
            console.error('Error saving driver expense:', error);
            showError('Failed to save driver expense: ' + error.message);
        }
    }

    function updateTotals(orders) {
        try {
            if (!Array.isArray(orders)) {
                throw new Error('Invalid orders data for totals calculation');
            }

            const totals = orders.reduce((acc, order) => ({
                cases: acc.cases + (parseInt(order.total_cases) || 0),
                cost: acc.cost + (parseFloat(order.total_cost) || 0),
                cashPayments: acc.cashPayments + (parseFloat(order.payment_cash) || 0),
                checkPayments: acc.checkPayments + (parseFloat(order.payment_check) || 0),
                creditPayments: acc.creditPayments + (parseFloat(order.payment_credit) || 0),
                totalPayments: acc.totalPayments + (parseFloat(order.payment_received) || 0)
            }), {
                cases: 0,
                cost: 0,
                cashPayments: 0,
                checkPayments: 0,
                creditPayments: 0,
                totalPayments: 0
            });

            // Safely update DOM elements
            const updateElement = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    if (id === 'totalCases' || id === 'tableTotalCases') {
                        element.textContent = value;
                    } else {
                        element.textContent = `$${parseFloat(value).toFixed(2)}`;
                    }
                }
            };

            updateElement('totalCases', totals.cases);
            updateElement('totalCost', totals.cost);
            updateElement('totalPayments', totals.totalPayments);
            updateElement('tableTotalCases', totals.cases);
            updateElement('tableTotalCost', totals.cost);
            updateElement('totalCashPayments', totals.cashPayments);
            updateElement('totalCheckPayments', totals.checkPayments);
            updateElement('totalCreditPayments', totals.creditPayments);
            updateElement('tableTotalPayments', totals.totalPayments);

        } catch (error) {
            console.error('Error updating totals:', error);
            showError('Failed to update totals: ' + error.message);
        }
    }

    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.alert-container').appendChild(alertDiv);
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    function showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.alert-container').appendChild(alertDiv);
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }

    // Initial setup
    updateAddOrderButton();
    loadDailyDriverExpense();
    loadCustomers();
});
